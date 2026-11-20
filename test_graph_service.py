import sys
sys.path.insert(0, "backend")

from app.services.graph_service import graph_service

try:
    print("\n--- GRAPH CONNECTION ---")
    print("Connected:", graph_service.connect())

    print("\n--- DISEASE CONTEXT TEST ---")
    context = graph_service.get_disease_context(
        "Oral Squamous Cell Carcinoma histopathology biomarkers diagnosis"
    )
    print("Retrieved records:", len(context))

    for item in context[:5]:
        print(item)

    print("\n--- CASE PERSISTENCE TEST ---")
    saved = graph_service.save_case(
        case_id="TEST-GRAPH-001",
        filename="test_image.jpg",
        patient_context={"age": "Not provided"},
        prediction_label="OSCC",
        probability=0.92,
        xai_summary={"test": True},
        user_question="Graph service integration test"
    )
    print("Case saved:", saved)

finally:
    graph_service.close()