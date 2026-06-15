from __future__ import annotations

import numpy as np

from app.services.face_similarity import (
    AnalyzedFace,
    DetectedFace,
    FaceAnalysisResult,
    FaceEmbedding,
    FaceLandmarks,
)


def test_face_embedding_public_dict_omits_raw_vector() -> None:
    embedding = FaceEmbedding(
        model="opencv-sface",
        generated=True,
        returned=False,
        dimension=128,
        vector=np.ones(128, dtype=np.float32),
    )

    public = embedding.to_public_dict()

    assert public == {
        "model": "opencv-sface",
        "generated": True,
        "returned": False,
        "dimension": 128,
    }
    assert "vector" not in public


def test_embedding_result_public_dict_keeps_embeddings_private() -> None:
    detected_face = DetectedFace(
        box=(1.0, 2.0, 3.0, 4.0),
        detection_score=0.99,
        landmarks=FaceLandmarks(
            right_eye=(5.0, 6.0),
            left_eye=(7.0, 8.0),
            nose_tip=(9.0, 10.0),
            right_mouth_corner=(11.0, 12.0),
            left_mouth_corner=(13.0, 14.0),
        ),
        raw_detection_row=np.array(
            [
                1.0,
                2.0,
                3.0,
                4.0,
                5.0,
                6.0,
                7.0,
                8.0,
                9.0,
                10.0,
                11.0,
                12.0,
                13.0,
                14.0,
                0.99,
            ],
            dtype=np.float32,
        ),
    )
    analyzed_face = AnalyzedFace(
        detection=detected_face,
        embedding=FaceEmbedding(
            model="opencv-sface",
            generated=True,
            returned=False,
            dimension=128,
            vector=np.arange(128, dtype=np.float32),
        ),
    )
    result = FaceAnalysisResult(
        object_name="face_similarity.embedding_result",
        model="celeba-face-similarity-cpu",
        mode="embedding_only",
        faces=[analyzed_face],
        disclaimer=(
            "Embeddings were generated internally. "
            "CelebA similarity matching is not implemented yet."
        ),
    )

    public = result.to_public_dict()

    assert public["object"] == "face_similarity.embedding_result"
    assert public["mode"] == "embedding_only"
    assert public["faces"][0]["embedding"]["generated"] is True
    assert public["faces"][0]["embedding"]["returned"] is False
    assert public["faces"][0]["embedding"]["dimension"] == 128
    assert "vector" not in public["faces"][0]["embedding"]
    assert public["faces"][0]["top_matches"] == []
