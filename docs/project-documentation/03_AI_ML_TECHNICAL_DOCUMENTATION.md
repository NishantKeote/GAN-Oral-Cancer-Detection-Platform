# 03. AI / ML Technical Documentation

## 1. Executive Summary & Model Inventory

The Artificial Intelligence and Machine Learning subsystem of the Oral Cancer Detection Platform provides histopathological image classification, multi-method Explainable AI (XAI) feature attribution, and dense vector similarity retrieval for literature grounding.

### 1.1 Model Artifact Inventory

| Model Component | Architecture / Model Type | Artifact Path | Size on Disk | Provenance / Training Status |
| :--- | :--- | :--- | :--- | :--- |
| **Histopathology Classifier** | EfficientNetB0 (Transfer Learning) | `models/best_efficientnetb0.keras` | 33.8 MB (35,465,584 bytes) | Pre-trained on ImageNet, fine-tuned on OSCC histopathology dataset |
| **XAI Feature Attribution** | Grad-CAM, Grad-CAM++, LayerCAM, HiResCAM | Computed dynamically via `top_conv` layer gradients | N/A (Algorithmic) | Extracted from `notebooks/OSCC_Integrated_GraphRAG_EfficientNet_XAI_FINAL_FIXED.ipynb` |
| **Sentence Embedding** | `all-MiniLM-L6-v2` (Sentence-Transformers) | HuggingFace Hub cache | ~80 MB (runtime download) | Pre-trained 384-dimensional dense semantic bi-encoder |
| **Vector Search Index** | FAISS `IndexFlatIP` (Inner Product) | `knowledge_base/oscc_literature.faiss` | 290 KB (290,527 bytes) | 189 literature chunks indexed at 384 dimensions |
| **CycleGAN / GAN Model** | **Completely Absent** | N/A | 0 bytes | **Not Implemented / Missing**. No generator/discriminator weights or training scripts exist in the repository |

---

## 2. Histopathology Classifier: EfficientNetB0

### 2.1 Architecture Specification
The primary diagnostic vision model is structured around the `EfficientNetB0` convolutional backbone with compound scaling:
- **Input Dimensions:** `(224, 224, 3)` (RGB, float32 scaled to `[0.0, 255.0]` before internal backbone normalization).
- **Backbone Sublayers:** 238 internal operations (Depthwise separable convolutions, Squeeze-and-Excitation blocks, Swish activations).
- **Target Feature Layer for XAI:** `top_conv` (Output shape: `(None, 7, 7, 1280)`).
- **Classification Head:**
  - `GlobalAveragePooling2D()`: Collapses `(7, 7, 1280)` to `(1280,)`.
  - `BatchNormalization()`: Normalizes latent feature distribution.
  - `Dropout(0.4)`: Regularization against histopathologic tile overfitting.
  - `Dense(1, activation='sigmoid')`: Scalar output probability $p \in [0.0, 1.0]$.
- **Framework & Format:** TensorFlow 2.15+ / Keras 3.x native `.keras` zip-container format.

### 2.2 Preprocessing Pipeline
The vision pipeline implemented in `backend/app/services/vision_service.py` (`VisionService.preprocess_image`) exactly replicates the research notebook:
1. **Decode:** Raw image bytes decoded via `PIL.Image.open(io.BytesIO(image_bytes)).convert("RGB")`.
2. **Resize:** Bicubic/bilinear interpolation to exact dimensions `(224, 224)`.
3. **Array Conversion:** Conversion to NumPy array `np.asarray(image, dtype=np.float32)`.
4. **Dimension Expansion:** Batch dimension prepended yielding shape `(1, 224, 224, 3)`.
5. **Backbone Normalization:** EfficientNetB0 native scaling expects input in range `[0, 255]`, internally applying zero-centering and variance scaling.

### 2.3 Decision Threshold & Operating Point
Unlike standard naive thresholds ($0.50$), the classification threshold was empirically optimized on the validation cohort using Youden's J statistic / F1 optimization:
- **Optimal Decision Threshold:** `0.850266`
- **Decision Logic:**
  $$\hat{y} = \begin{cases} \text{Oral Squamous Cell Carcinoma (OSCC)}, & \text{if } p \ge 0.850266 \\ \text{Normal / Non-Cancerous Tissue}, & \text{if } p < 0.850266 \end{cases}$$
- **Confidence Calibration:**
  $$\text{Confidence Score} = \begin{cases} p, & \text{if } p \ge 0.850266 \\ 1.0 - p, & \text{if } p < 0.850266 \end{cases}$$

### 2.4 Empirical Test Set Performance
The verified performance metrics documented in `results/evaluation_metrics.json` and `results/` evaluation plots reflect test set evaluation on 500 test images (400 OSCC, 100 Normal):

| Metric | Measured Value | Standard Error / Notes |
| :--- | :--- | :--- |
| **Accuracy** | **94.79%** | Overall tile classification correctness |
| **Sensitivity (Recall)** | **89.56%** | True positive detection rate for malignant lesions |
| **Specificity** | **100.00%** | Zero false positives observed on test set normal tissue |
| **Precision (PPV)** | **100.00%** | High positive predictive value governed by optimal 0.850 threshold |
| **F1-Score** | **0.9449** | Harmonic mean of precision and recall |
| **ROC-AUC** | **0.9933** | Area under Receiver Operating Characteristic curve |
| **Optimal Threshold** | **0.850266** | Calibrated cut-off balancing false negatives and false positives |

> [!NOTE]
> These metrics apply to isolated 224x224 pixel histopathology image patches. They do not represent patient-level or biopsy-level diagnostic accuracy, which requires whole-slide image (WSI) aggregation.

---

## 3. Explainable AI (XAI) Attribution Pipeline

The XAI subsystem in `backend/app/services/xai_service.py` generates four distinct saliency visual heatmaps highlighting morphological regions influencing model predictions.

```
Input Image (224, 224, 3)
           │
           ▼
 EfficientNetB0 Forward Pass ───► Target Layer: 'top_conv' (7, 7, 1280)
           │                                 │
           │                     Gradient Tape Calculations
           │                                 │
           │        ┌──────────────┬─────────┴──────┬──────────────┐
           │        ▼              ▼                ▼              ▼
           │    Grad-CAM       Grad-CAM++        LayerCAM       HiResCAM
           │        │              │                │              │
           └───────►┼──────────────┼────────────────┼──────────────┤
                    ▼              ▼                ▼              ▼
                Jet Overlay    Jet Overlay      Jet Overlay    Jet Overlay
```

### 3.1 Mathematical Formulations

#### 1. Grad-CAM (Gradient-weighted Class Activation Mapping)
Calculates global average pooled gradients of the target class score $y^c$ with respect to feature activation maps $A^k$:
$$\alpha_k^c = \frac{1}{Z} \sum_{i} \sum_{j} \frac{\partial y^c}{\partial A_{i,j}^k}$$
$$L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c A^k\right)$$

#### 2. Grad-CAM++ (Second & Third Order Derivative Weighting)
Enhances localization of multiple occurrences of an object or heterogeneous morphological structures by weighting positive partial derivatives:
$$\alpha_{i,j}^{k,c} = \frac{\frac{\partial^2 y^c}{(\partial A_{i,j}^k)^2}}{2 \frac{\partial^2 y^c}{(\partial A_{i,j}^k)^2} + \sum_{a,b} A_{a,b}^k \frac{\partial^3 y^c}{(\partial A_{i,j}^k)^3}}$$
$$w_k^c = \sum_{i} \sum_{j} \alpha_{i,j}^{k,c} \cdot \text{ReLU}\left(\frac{\partial y^c}{\partial A_{i,j}^k}\right)$$
$$L_{\text{Grad-CAM++}}^c = \text{ReLU}\left(\sum_k w_k^c A^k\right)$$

#### 3. LayerCAM (Element-wise Spatial Attribution)
Computes fine-grained spatial attribution by retaining spatial positive gradient coordinates directly:
$$w_{i,j}^k = \text{ReLU}\left(\frac{\partial y^c}{\partial A_{i,j}^k}\right)$$
$$L_{\text{LayerCAM}}^c = \text{ReLU}\left(\sum_k w_{i,j}^k \cdot A_{i,j}^k\right)$$

#### 4. HiResCAM (Element-wise Product Preservation)
Eliminates spatial averaging artifacts by multiplying raw gradients directly with feature activations element-wise:
$$L_{\text{HiResCAM}}^c = \text{ReLU}\left(\sum_k \frac{\partial y^c}{\partial A_{i,j}^k} \cdot A_{i,j}^k\right)$$

### 3.2 Visualization & Artifact Generation
- **Normalization:** Heatmap tensors are normalized to $[0.0, 1.0]$ via min-max scaling:
  $$H_{\text{norm}} = \frac{H - \min(H)}{\max(H) - \min(H) + \epsilon}$$
- **Color Mapping:** `cv2.applyColorMap(np.uint8(255 * H_norm), cv2.COLORMAP_JET)`.
- **Blending:** Alpha-blended with original RGB image at $\alpha = 0.40$:
  $$I_{\text{overlay}} = \text{clip}\left(0.4 \times I_{\text{heatmap}} + 0.6 \times I_{\text{orig}}, 0, 255\right)$$
- **Output Storage:** Persisted as PNG files in `artifacts/{case_id}/{method}.png`.

---

## 4. Vector Literature Retrieval (RAG)

### 4.1 Embedding Model
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Output Embedding Dimension:** 384 dimensions
- **Normalization:** L2 unit norm applied to query embeddings prior to inner-product search.

### 4.2 FAISS Vector Index
- **Index Type:** `faiss.IndexFlatIP` (Inner Product on normalized vectors, mathematically equivalent to Cosine Similarity).
- **Index File:** `knowledge_base/oscc_literature.faiss` (Size: 290 KB, 189 total vectors).
- **Metadata Store:** `knowledge_base/chunk_metadata.json` (Size: 345 KB, 189 structured JSON objects).

### 4.3 Retrieval Algorithm & Score Conversion
1. Query string embedded: $\mathbf{q} \in \mathbb{R}^{384}$.
2. Normalization: $\mathbf{q}_{\text{norm}} = \frac{\mathbf{q}}{\|\mathbf{q}\|_2}$.
3. Vector search: `index.search(q_norm, top_k=3)` returning distances $s \in [-1.0, 1.0]$ and indices.
4. Similarity Score Transformation: Converted to a human-readable similarity percentage:
   $$\text{Score} = \text{clamp}\left(\frac{s + 1.0}{2.0}, 0.0, 1.0\right)$$
5. Metadata joining: Look up chunk by integer index, returning `chunk_id`, `paper_id`, `year`, `title`, `authors`, `source_url`, and `text`.

---

## 5. Critical Audit: CycleGAN Absence Statement

> [!WARNING]
> ### Rigorous Audit Finding: Complete Absence of CycleGAN Implementation
> 
> The project repository title is **`GAN-based-Oral-Cancer-detection-with-GraphRag-GradCam`** and prior informal documentation referenced CycleGAN synthetic data generation (claiming 100 training epochs, MAE 0.0918, and Identity Loss 0.0600).
> 
> **Repository Ground Truth:**
> 1. **No GAN Source Code:** There are no Python scripts, Keras models, or PyTorch definitions for generator ($G_{A \to B}, G_{B \to A}$) or discriminator ($D_A, D_B$) networks.
> 2. **No GAN Weights:** No `.h5`, `.keras`, `.pt`, or `.onnx` model weights for any GAN architecture exist in the repository.
> 3. **No Synthetic Training Data:** No paired or unpaired synthetic histopathology image datasets are present.
> 4. **Inference Pipeline Decoupling:** The end-to-end inference pipeline (`analysis_service.py`) operates solely on the input image directly into `EfficientNetB0`.
> 
> **Architectural Conclusion:** The classification and explainability pipelines are 100% functional without a GAN. Any references to GAN training in previous documentation reflect uncommitted external research experiments or theoretical design proposals.
