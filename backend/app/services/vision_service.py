"""EfficientNetB0 Vision Service Module.

Extracted from:
notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb (Cells 2, 3, 7)

Responsibilities:
- Thread-safe singleton loading of the trained EfficientNetB0 Keras model.
- Faithful reproduction of the original image preprocessing contract (224x224 RGB, clipping, EfficientNet scaling).
- Forward inference returning continuous OSCC sigmoid score, classification verdict against threshold 0.850266,
  and prediction confidence metrics.
- Strict input validation and safe error handling without exposing filesystem internals or secrets.
"""

from pathlib import Path
import threading
from typing import Any, Dict, Optional, Tuple
from app.config import settings
from app.core.logging import logger

IMAGE_SIZE: Tuple[int, int] = (224, 224)
DEFAULT_THRESHOLD: float = 0.850266
CLASS_MAPPING: Dict[str, int] = {"Normal": 0, "OSCC": 1}
CLASS_INDEX_TO_LABEL: Dict[int, str] = {0: "Normal", 1: "OSCC"}


class VisionService:
    """Manages EfficientNetB0 model loading, image preprocessing, and inference."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        threshold: Optional[float] = None,
    ) -> None:
        """Initialize the VisionService with model path and classification threshold."""
        self.model_path: Path = model_path or settings.MODEL_PATH
        self.threshold: float = threshold if threshold is not None else settings.CLASSIFICATION_THRESHOLD
        self._model: Any = None
        self._is_loaded: bool = False
        self._lock: threading.Lock = threading.Lock()
        self.image_size: Tuple[int, int] = IMAGE_SIZE
        self.class_mapping: Dict[str, int] = CLASS_MAPPING

    @property
    def is_loaded(self) -> bool:
        """Return True if the model has been loaded into memory."""
        return self._is_loaded

    @property
    def model(self) -> Any:
        """Return the underlying Keras model instance, loading if necessary."""
        self.ensure_model_loaded()
        return self._model

    def load_model(self) -> None:
        """Load the trained Keras 3 model once from disk and validate shapes.

        Preserves the exact assertions from Notebook Cell 3:
        - input_shape: (None, 224, 224, 3)
        - output_shape: (None, 1)
        """
        with self._lock:
            if self._is_loaded and self._model is not None:
                return

            if not self.model_path.is_file():
                err_msg = f"Trained model checkpoint not found at: {self.model_path}"
                logger.error(err_msg)
                raise FileNotFoundError(err_msg)

            try:
                import tensorflow as tf
            except ImportError as exc:
                err_msg = "TensorFlow is not installed in the active environment."
                logger.error("%s Detail: %s", err_msg, exc)
                raise RuntimeError(err_msg) from exc

            logger.info("Loading EfficientNetB0 model from: %s", self.model_path)
            try:
                loaded_model = tf.keras.models.load_model(str(self.model_path), compile=False)
            except Exception as exc:
                logger.exception("Failed to load Keras model from %s", self.model_path)
                raise RuntimeError(f"Failed to load Keras model: {exc}") from exc

            # Verify model contract matches the notebook specifications
            input_shape = tuple(loaded_model.input_shape[1:])
            output_shape = tuple(loaded_model.output_shape[1:])

            if input_shape != (224, 224, 3):
                raise ValueError(
                    f"Invalid model input shape {loaded_model.input_shape}; expected (None, 224, 224, 3)"
                )
            if output_shape != (1,):
                raise ValueError(
                    f"Invalid model output shape {loaded_model.output_shape}; expected (None, 1)"
                )

            self._model = loaded_model
            self._is_loaded = True
            logger.info(
                "EfficientNetB0 successfully loaded. Input: %s, Output: %s, Threshold: %f",
                self._model.input_shape,
                self._model.output_shape,
                self.threshold,
            )

    def ensure_model_loaded(self) -> None:
        """Thread-safe helper ensuring model is initialized before inference."""
        if not self._is_loaded:
            self.load_model()

    def preprocess_image_bytes(self, image_bytes: bytes) -> Tuple[Any, Any]:
        """Preprocess raw image bytes into normalized model input tensor and RGB array.

        Preserves the exact pipeline from Notebook Cell 7:
        1. tf.io.decode_image(..., channels=3, expand_animations=False)
        2. Set shape [None, None, 3]
        3. tf.image.resize(..., (224, 224), antialias=True)
        4. tf.cast(..., tf.float32) [retains 0.0 - 255.0 range]
        5. tf.clip_by_value(..., 0.0, 255.0)
        6. Assert finite and values within [0.0, 255.0]
        7. tf.keras.applications.efficientnet.preprocess_input(resized)
        8. Return (model_input[None, ...], uint8 RGB numpy array)

        Args:
            image_bytes: Raw binary bytes of uploaded image.

        Returns:
            Tuple containing:
            - model_input: Tensor of shape (1, 224, 224, 3) ready for inference.
            - rgb_image: NumPy uint8 array of shape (224, 224, 3) for overlays.
        """
        if not image_bytes:
            raise ValueError("Uploaded image bytes are empty.")

        try:
            import numpy as np
            import tensorflow as tf
        except ImportError as exc:
            raise RuntimeError("TensorFlow / NumPy is not installed in the active environment.") from exc

        try:
            decoded = tf.io.decode_image(tf.convert_to_tensor(image_bytes), channels=3, expand_animations=False)
            decoded.set_shape([None, None, 3])

            resized = tf.image.resize(decoded, self.image_size, antialias=True)
            resized = tf.cast(resized, tf.float32)
            resized = tf.clip_by_value(resized, clip_value_min=0.0, clip_value_max=255.0)

            tf.debugging.assert_all_finite(resized, "Non-finite image input")
            tf.debugging.assert_greater_equal(tf.reduce_min(resized), 0.0)
            tf.debugging.assert_less_equal(tf.reduce_max(resized), 255.0)

            model_input = tf.keras.applications.efficientnet.preprocess_input(resized)
            rgb_image = np.clip(resized.numpy(), 0, 255).astype(np.uint8)

            return model_input[None, ...], rgb_image

        except Exception as exc:
            logger.warning("Image decoding and preprocessing failed: %s", exc)
            raise ValueError(f"Image could not be decoded or preprocessed: {exc}") from exc

    def predict(self, image_bytes: bytes) -> Dict[str, Any]:
        """Execute end-to-end classification on uploaded image bytes.

        Preserves the exact prediction logic and decision threshold from Notebook Cell 7:
        - probability = float(model(image_tensor, training=False).numpy().reshape(-1)[0])
        - label = 'OSCC' if probability >= CLASSIFICATION_THRESHOLD else 'Normal'
        - confidence = probability if label == 'OSCC' else 1.0 - probability

        Args:
            image_bytes: Raw binary bytes of uploaded histopathology image.

        Returns:
            Dictionary with inference outputs:
            - image_tensor: Preprocessed tensor (1, 224, 224, 3)
            - rgb_image: uint8 array (224, 224, 3)
            - oscc_probability: Continuous sigmoid score in [0.0, 1.0]
            - prediction: Class label ('OSCC' or 'Normal')
            - class_index: Integer index (0 for Normal, 1 for OSCC)
            - confidence: Class-specific confidence score in [0.0, 1.0]
            - confidence_percent: Confidence expressed as percentage [0.0 - 100.0]
            - threshold: Decision threshold applied (0.850266)
            - decision_rule: Textual description of decision rule
        """
        self.ensure_model_loaded()

        image_tensor, rgb_image = self.preprocess_image_bytes(image_bytes)

        try:
            raw_output = self._model(image_tensor, training=False)
            probability = float(raw_output.numpy().reshape(-1)[0])
        except Exception as exc:
            logger.exception("Model forward pass failed during inference.")
            raise RuntimeError(f"Model forward pass execution error: {exc}") from exc

        label = "OSCC" if probability >= self.threshold else "Normal"
        confidence = probability if label == "OSCC" else 1.0 - probability
        class_index = self.class_mapping[label]

        logger.info(
            "Inference complete: verdict=%s, score=%.6f, threshold=%.6f, confidence=%.2f%%",
            label,
            probability,
            self.threshold,
            confidence * 100.0,
        )

        return {
            "image_tensor": image_tensor,
            "rgb_image": rgb_image,
            "oscc_probability": probability,
            "prediction": label,
            "class_index": class_index,
            "confidence": float(confidence),
            "confidence_percent": round(confidence * 100.0, 2),
            "threshold": float(self.threshold),
            "decision_rule": f"OSCC when OSCC sigmoid score >= {self.threshold:.6f}; otherwise Normal",
        }


# Global singleton instance
vision_service = VisionService()
