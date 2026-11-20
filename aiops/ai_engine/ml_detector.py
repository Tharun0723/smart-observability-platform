
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def detect_ml_anomaly(historical_data, current_metrics):

    if len(historical_data) < 5:
        return {
            "ml_status": "insufficient_data",
            "ml_anomaly": False,
            "message": "Not enough historical data for ML detection."
        }

    # Use metrics available in both historical and current data.
    metric_names = [
        key for key in current_metrics
        if key in historical_data[0]
        and isinstance(current_metrics[key], (int, float))
        and not isinstance(current_metrics[key], bool)
    ]

    if not metric_names:
        return {
            "ml_status": "invalid_data",
            "ml_anomaly": False,
            "message": "No compatible numeric metrics found."
        }

    # Prepare historical training data.
    X_train = []

    for record in historical_data:
        row = []

        for metric in metric_names:
            value = record.get(metric)

            if not isinstance(value, (int, float)) or isinstance(value, bool):
                value = np.nan

            row.append(value)

        X_train.append(row)

    X_train = np.array(X_train, dtype=float)

    # Replace missing values with each metric's historical median.
    medians = np.nanmedian(X_train, axis=0)
    medians = np.nan_to_num(medians, nan=0.0)

    for column in range(X_train.shape[1]):
        X_train[np.isnan(X_train[:, column]), column] = medians[column]

    # Prepare current observation.
    current_row = []

    for metric in metric_names:
        current_row.append(float(current_metrics[metric]))

    X_current = np.array([current_row], dtype=float)

    # Train Isolation Forest using historical telemetry.
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("isolation_forest", IsolationForest(
            contamination="auto",
            random_state=42,
            n_estimators=100
        ))
    ])

    model.fit(X_train)

    prediction = model.predict(X_current)[0]
    anomaly_score = model.decision_function(X_current)[0]

    is_anomaly = prediction == -1

    return {
        "ml_status": "success",
        "ml_anomaly": bool(is_anomaly),
        "ml_score": round(float(anomaly_score), 4),
        "detected_by": "Isolation Forest" if is_anomaly else None,
        "message": (
            "ML detected an unusual telemetry pattern."
            if is_anomaly
            else "ML did not detect an unusual telemetry pattern."
        )
    }
