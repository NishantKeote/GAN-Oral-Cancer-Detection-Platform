"""Explainable AI (XAI) Attribution Service Module.

Extracted from:
notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb (Cell 7)

Responsibilities:
- Reuses the loaded EfficientNetB0 Keras model from VisionService (zero redundant copies).
- Attaches intermediate probe to layer 'efficientnetb0/top_conv' with output shape (None, 7, 7, 1280).
- Single-pass persistent gradient tape extraction providing activations and gradients.
- Faithful mathematical derivation and rendering of four attribution methods:
    1. Grad-CAM (Global-average-pooled gradient weighting)
    2. Grad-CAM++ (Higher-order derivative weighting on continuous sigmoid score)
    3. LayerCAM (Element-wise positive gradient weighting)
    4. HiResCAM (Element-wise raw gradient product)
- Safe bilinear resizing to (224, 224) and min-max normalization to [0.0, 1.0].
- Alpha-blended RGB overlay rendering (0.58 * RGB + 0.42 * Red_Heatmap).
- Per-method statistical summaries and full pairwise Pearson & Cosine cross-method agreement metrics.
- Thread-safe lazy probe initialization and robust error recovery.
"""

from pathlib import Path
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from app.config import settings
from app.core.logging import logger
from app.services.vision_service import vision_service

IMAGE_SIZE: Tuple[int, int] = (224, 224)
XAI_METHOD_NAMES: List[str] = ["Grad-CAM", "Grad-CAM++", "LayerCAM", "HiResCAM"]
XAI_FILE_NAMES: Dict[str, str] = {
    "Grad-CAM": "grad_cam",
    "Grad-CAM++": "grad_cam_plus_plus",
    "LayerCAM": "layer_cam",
    "HiResCAM": "hires_cam",
}


class XAIService:
    """Manages computation and rendering of the four attribution methods."""

    def __init__(self, artifact_dir: Optional[Path] = None) -> None:
        """Initialize the XAIService with artifact storage directory."""
        self.artifact_dir: Path = artifact_dir or settings.ARTIFACT_DIR
        self.method_names: List[str] = XAI_METHOD_NAMES
        self.file_names: Dict[str, str] = XAI_FILE_NAMES

        # Probe and layer references
        self._conv_probe: Any = None
        self._backbone: Any = None
        self._last_conv: Any = None
        self._backbone_index: int = -1
        self._head_layers: List[Any] = []
        self._output_layer: Any = None
        self._is_initialized: bool = False
        self._lock: threading.Lock = threading.Lock()

    @property
    def is_initialized(self) -> bool:
        """Return True if the convolutional probe has been constructed."""
        return self._is_initialized

    def _inference_call(self, layer: Any, x: Any) -> Any:
        """Call layer in inference mode, gracefully handling layers without a training kwarg."""
        try:
            return layer(x, training=False)
        except TypeError:
            return layer(x)

    def _ensure_probe_initialized(self) -> None:
        """Construct the intermediate convolutional probe model from VisionService.

        Preserves exact assertions and layer wiring from Notebook Cell 7:
        - backbone = model.get_layer('efficientnetb0')
        - last_conv = backbone.get_layer('top_conv')
        - backbone.output_shape: (None, 7, 7, 1280)
        - last_conv.output.shape: (None, 7, 7, 1280)
        - output_layer: Dense(1, activation='sigmoid')
        """
        with self._lock:
            if self._is_initialized and self._conv_probe is not None:
                return

            try:
                import tensorflow as tf
            except ImportError as exc:
                raise RuntimeError("TensorFlow is not installed in the active environment.") from exc

            # Ensure the vision service model is loaded into memory
            model = vision_service.model
            if model is None:
                raise RuntimeError("Cannot initialize XAI probe: VisionService model is None.")

            logger.info("Initializing XAI convolutional probe from loaded EfficientNetB0 backbone...")

            try:
                self._backbone = model.get_layer("efficientnetb0")
                self._last_conv = self._backbone.get_layer("top_conv")
            except ValueError as exc:
                logger.exception("Failed to locate required layers ('efficientnetb0', 'top_conv') in model.")
                raise ValueError(f"Model architecture incompatible with XAI probe: {exc}") from exc

            # Verify layer output tensor shapes
            backbone_shape = tuple(self._backbone.output_shape[1:])
            last_conv_shape = tuple(self._last_conv.output.shape[1:])
            if backbone_shape != (7, 7, 1280):
                raise ValueError(f"Unexpected backbone output shape: {backbone_shape}; expected (7, 7, 1280)")
            if last_conv_shape != (7, 7, 1280):
                raise ValueError(f"Unexpected top_conv output shape: {last_conv_shape}; expected (7, 7, 1280)")

            self._backbone_index = model.layers.index(self._backbone)
            self._head_layers = model.layers[self._backbone_index + 1 : -1]
            self._output_layer = model.layers[-1]

            # Validate classifier head layers
            allowed_head = (
                tf.keras.layers.GlobalAveragePooling2D,
                tf.keras.layers.GlobalMaxPooling2D,
                tf.keras.layers.Flatten,
                tf.keras.layers.BatchNormalization,
                tf.keras.layers.Dropout,
                tf.keras.layers.Dense,
                tf.keras.layers.ReLU,
                tf.keras.layers.Activation,
            )
            unsupported = [(l.name, type(l).__name__) for l in self._head_layers if not isinstance(l, allowed_head)]
            if unsupported:
                raise ValueError(f"Unsupported classifier head for analytic Grad-CAM++: {unsupported}")

            for layer in self._head_layers:
                if isinstance(layer, (tf.keras.layers.Dense, tf.keras.layers.Activation)):
                    act = tf.keras.activations.serialize(layer.activation)
                    if act not in ("linear", "relu"):
                        raise ValueError(f"Unsupported activation '{act}' in layer '{layer.name}'")

            if not (isinstance(self._output_layer, tf.keras.layers.Dense) and self._output_layer.units == 1):
                raise ValueError(f"Output layer must be Dense(1); found {self._output_layer}")
            if tf.keras.activations.serialize(self._output_layer.activation) != "sigmoid":
                raise ValueError(f"Output layer activation must be sigmoid; found {self._output_layer.activation}")

            # Construct intermediate probe capturing both top_conv and backbone pooling output
            self._conv_probe = tf.keras.Model(
                self._backbone.input,
                [self._last_conv.output, self._backbone.output],
                name="trained_efficientnetb0_conv_probe",
            )
            self._is_initialized = True
            logger.info("XAI convolutional probe successfully constructed and verified.")

    def _run_model_prefix(self, x: Any) -> Any:
        """Replay prefix layers before the backbone to keep gradient graph connected."""
        model = vision_service.model
        z = x
        for layer in model.layers[1 : self._backbone_index]:
            z = self._inference_call(layer, z)
        return z

    def _head_logits_from_backbone_output(self, backbone_output: Any) -> Any:
        """Replay classifier head layers to derive exact pre-sigmoid logits."""
        import tensorflow as tf

        z = backbone_output
        for layer in self._head_layers:
            z = self._inference_call(layer, z)
        if self._output_layer.use_bias:
            return tf.linalg.matmul(z, self._output_layer.kernel) + self._output_layer.bias
        return tf.linalg.matmul(z, self._output_layer.kernel)

    def _resize_normalize(self, raw: Any) -> Any:
        """Bilinear resize raw attribution map to (224, 224) and normalize to [0, 1].

        Preserves exact logic from Notebook Cell 7:
        - method='bilinear', antialias=False
        - replace non-finite values with 0
        - per-image min-max divide_no_nan
        """
        import tensorflow as tf

        heat = tf.image.resize(raw[None, ..., None], IMAGE_SIZE, method="bilinear", antialias=False)[0, ..., 0]
        heat = tf.where(tf.math.is_finite(heat), heat, tf.zeros_like(heat))
        lo = tf.reduce_min(heat)
        hi = tf.reduce_max(heat)
        return tf.math.divide_no_nan(heat - lo, hi - lo)

    def _heatmap_similarity(self, maps: Dict[str, Any]) -> Dict[str, Dict[str, Optional[float]]]:
        """Compute pairwise Pearson correlation and Cosine similarity across all map pairs.

        Preserves exact logic from Notebook Cell 7.
        """
        import numpy as np

        names = list(maps)
        result: Dict[str, Dict[str, Optional[float]]] = {}
        for i, a_name in enumerate(names):
            for b_name in names[i + 1 :]:
                a = maps[a_name].reshape(-1).astype(np.float64)
                b = maps[b_name].reshape(-1).astype(np.float64)
                ac = a - a.mean()
                bc = b - b.mean()
                denom = float(np.linalg.norm(ac) * np.linalg.norm(bc))
                cden = float(np.linalg.norm(a) * np.linalg.norm(b))
                result[f"{a_name} vs {b_name}"] = {
                    "pearson_correlation": float(np.dot(ac, bc) / denom) if denom else None,
                    "cosine_similarity": float(np.dot(a, b) / cden) if cden else None,
                }
        return result

    def _failed_method(self, exc: Exception) -> Dict[str, Any]:
        """Standardized payload returned when an individual attribution method fails."""
        return {
            "status": "failed",
            "error": type(exc).__name__,
            "heatmap_path": None,
            "heatmap_url": None,
            "overlay_path": None,
            "overlay_url": None,
            "normalization": "Per-image min-max to [0,1]; constant maps are zero.",
        }

    def generate_attributions(
        self,
        image_tensor: Any,
        rgb_image: Any,
        case_id: str,
        expected_probability: float,
    ) -> Dict[str, Any]:
        """Compute all four Explainable AI attribution methods and save PNG artifacts.

        Preserves exact single-pass gradient tape extraction, analytical Grad-CAM++
        higher-order derivatives, normalization, and overlay blending from Notebook Cell 7.

        Args:
            image_tensor: Normalized model input tensor (1, 224, 224, 3).
            rgb_image: Original RGB image array (224, 224, 3) with uint8 values in [0, 255].
            case_id: Standardized case identifier string (e.g. 'CASE-4F8A9C12DE').
            expected_probability: Full model prediction probability for equivalence assertion.

        Returns:
            Dictionary matching Pydantic XAISummary schema with per-method results,
            heatmaps, overlays, statistics, and pairwise cross-method correlations.
        """
        try:
            import numpy as np
            from PIL import Image
            import tensorflow as tf
        except ImportError as exc:
            raise RuntimeError("TensorFlow, NumPy, or Pillow is not installed in the active environment.") from exc

        methods: Dict[str, Any] = {
            name: {"status": "failed", "error": "shared_gradient_extraction_failed"}
            for name in self.method_names
        }

        try:
            self._ensure_probe_initialized()

            # Single forward-backward pass under persistent tape serving all four methods
            with tf.GradientTape(persistent=True) as tape:
                prefix = self._run_model_prefix(image_tensor)
                activations, backbone_output = self._conv_probe(prefix, training=False)
                logits = self._head_logits_from_backbone_output(backbone_output)
                score = tf.math.sigmoid(logits)

            score_gradient = tape.gradient(score, activations)
            logit_gradient = tape.gradient(logits, activations)
            del tape

            # Verify prediction equivalence between intermediate probe and full forward pass
            probe_probability = float(score.numpy().reshape(-1)[0])
            np.testing.assert_allclose(probe_probability, expected_probability, rtol=2e-4, atol=2e-5)

            A = activations[0]
            G = score_gradient[0]
            GL = logit_gradient[0]

            # Analytic higher-order derivatives for Grad-CAM++ (exact reproduction of Cell 7)
            p = tf.clip_by_value(tf.reshape(score, []), tf.keras.backend.epsilon(), 1.0 - tf.keras.backend.epsilon())
            s1 = p * (1.0 - p)
            s2 = s1 * (1.0 - 2.0 * p)
            s3 = s1 * (1.0 - 6.0 * p + 6.0 * tf.square(p))
            d1 = s1 * GL
            d2 = s2 * tf.square(GL)
            d3 = s3 * tf.pow(GL, 3)
            sum_A = tf.reduce_sum(A, axis=[0, 1], keepdims=True)
            alpha_pp = tf.math.divide_no_nan(d2, 2.0 * d2 + sum_A * d3)
            weights_pp = tf.reduce_sum(alpha_pp * tf.nn.relu(d1), axis=[0, 1], keepdims=True)

            # Define mathematical formulas for all four attribution methods
            raw_methods: Dict[str, Callable[[], Any]] = {
                "Grad-CAM": lambda: tf.nn.relu(tf.reduce_sum(A * tf.reduce_mean(G, axis=[0, 1], keepdims=True), axis=-1)),
                "Grad-CAM++": lambda: tf.nn.relu(tf.reduce_sum(weights_pp * A, axis=-1)),
                "LayerCAM": lambda: tf.nn.relu(tf.reduce_sum(A * tf.nn.relu(G), axis=-1)),
                "HiResCAM": lambda: tf.nn.relu(tf.reduce_sum(A * G, axis=-1)),
            }

            maps: Dict[str, Any] = {}
            case_dir = self.artifact_dir / case_id
            case_dir.mkdir(parents=True, exist_ok=True)

            for method in self.method_names:
                try:
                    normalized = self._resize_normalize(raw_methods[method]()).numpy()
                    if not np.isfinite(normalized).all():
                        raise ValueError("non_finite_heatmap")

                    maps[method] = normalized

                    stats = {
                        "min": float(normalized.min()),
                        "max": float(normalized.max()),
                        "mean": float(normalized.mean()),
                        "std": float(normalized.std()),
                        "q90": float(np.quantile(normalized, 0.90)),
                        "fraction_at_or_above_0_5": float(np.mean(normalized >= 0.5)),
                    }

                    stem = self.file_names[method]
                    heat_name = stem + ".png"
                    overlay_name = stem + "_overlay.png"

                    # 1. Grayscale Heatmap PNG (mode='L')
                    heat8 = np.clip(normalized * 255.0, 0, 255).astype(np.uint8)
                    Image.fromarray(heat8, mode="L").save(case_dir / heat_name)

                    # 2. RGB Overlay PNG (0.58*RGB + 0.42*Red, mode='RGB')
                    red = np.zeros_like(rgb_image)
                    red[..., 0] = heat8
                    overlay = np.clip(0.58 * rgb_image.astype(np.float32) + 0.42 * red.astype(np.float32), 0, 255).astype(np.uint8)
                    Image.fromarray(overlay, mode="RGB").save(case_dir / overlay_name)

                    methods[method] = {
                        "status": "ok",
                        "heatmap_path": str(case_dir / heat_name),
                        "heatmap_url": f"/heatmaps/{case_id}/{heat_name}",
                        "overlay_path": str(case_dir / overlay_name),
                        "overlay_url": f"/heatmaps/{case_id}/{overlay_name}",
                        "normalization": "Per-image min-max to [0,1] after method ReLU; constant maps are zero.",
                        "statistics": stats,
                    }

                except Exception as exc:
                    logger.warning("Attribution method '%s' failed for case '%s': %s", method, case_id, exc)
                    methods[method] = self._failed_method(exc)

            similarity = self._heatmap_similarity(maps)

            logger.info("XAI attribution successfully generated for case '%s'. All 4 methods computed.", case_id)

            return {
                "target": "continuous OSCC sigmoid score",
                "prediction_equivalence_verified": True,
                "methods": methods,
                "pairwise_similarity": similarity,
                "scope_note": "Attribution only; not lesion detection, pathology confirmation, or evidence of cancer.",
            }

        except Exception as exc:
            logger.exception("Shared gradient extraction failed for case '%s': %s", case_id, exc)
            return {
                "target": "continuous OSCC sigmoid score",
                "prediction_equivalence_verified": False,
                "methods": {name: self._failed_method(exc) for name in self.method_names},
                "pairwise_similarity": {},
                "scope_note": "Attribution only; not lesion detection, pathology confirmation, or evidence of cancer.",
            }


# Global singleton instance
xai_service = XAIService()
