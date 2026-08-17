import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run YOLO inference for Visions15.")
    parser.add_argument("image_path")
    parser.add_argument("--model", required=True)
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--confidence", type=float, default=0.35)
    args = parser.parse_args()

    image_path = Path(args.image_path)
    model_path = Path(args.model)
    export_dir = Path(args.export_dir)

    if not image_path.is_file():
        raise FileNotFoundError(f"Изображение не найдено: {image_path}")
    if not model_path.is_file():
        raise FileNotFoundError(f"Файл модели не найден: {model_path}")

    export_dir.mkdir(parents=True, exist_ok=True)

    from ultralytics import YOLO

    model = YOLO(str(model_path))
    results = model(
        str(image_path),
        conf=args.confidence,
        device=args.device,
        verbose=False,
    )

    predictions = []
    for result in results:
        names = result.names
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            predictions.append(
                {
                    "category_name": str(names[class_id]),
                    "score": float(box.conf[0].item()),
                    "bbox_xyxy": [float(value) for value in box.xyxy[0].detach().cpu().tolist()],
                }
            )

    visual_path = save_prediction_visual(results, export_dir)

    print(
        json.dumps(
            {
                "image_path": str(image_path),
                "export_dir": str(export_dir),
                "visual_path": str(visual_path) if visual_path else None,
                "predictions": predictions,
            },
            ensure_ascii=False,
        )
    )
    return 0


def save_prediction_visual(results, export_dir):
    if not results:
        return None

    visual_path = export_dir / "prediction_visual.jpg"

    try:
        plotted_image = results[0].plot()
        import cv2

        if cv2.imwrite(str(visual_path), plotted_image):
            return visual_path
    except Exception:
        return None

    return None


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
