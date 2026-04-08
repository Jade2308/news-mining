"""Evaluation script for PhoBERT clickbait classifier"""
import torch
import pandas as pd
import logging
import json
import os
import sys
from pathlib import Path
from sklearn.metrics import (
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve
)
import matplotlib.pyplot as plt
import numpy as np

# Ensure project root is in Python path when running as script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import MODEL_DIR, DATASET_CSV, EVALUATION_DIR
from models.phobert_classifier import PhoBERTClickbaitClassifier
from sklearn.model_selection import train_test_split

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def evaluate_model(
    model_path: str = str(MODEL_DIR),
    csv_path: str = DATASET_CSV,
    output_dir: str = str(EVALUATION_DIR),
    test_size: float = 0.2,
    seed: int = 42
):
    """Evaluate PhoBERT model on test set.
    
    Args:
        model_path: Path to fine-tuned model
        csv_path: Path to dataset CSV
        output_dir: Directory to save evaluation results
        test_size: Test set ratio
        seed: Random seed
    """
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    logger.info(f"📂 Loading dataset from {csv_path}")
    df = pd.read_csv(csv_path)
    
    texts = df['title'].tolist()
    labels = [1 if str(label).lower().strip() == 'clickbait' else 0 
              for label in df['label']]
    
    # Split data
    _, test_texts, _, test_labels = train_test_split(
        texts, labels, test_size=test_size, random_state=seed, stratify=labels
    )
    
    logger.info(f"📊 Test set size: {len(test_texts)}")
    logger.info(f"   Clickbait: {sum(test_labels)}")
    logger.info(f"   Non-clickbait: {len(test_labels) - sum(test_labels)}")
    
    # Load model
    logger.info(f"🤖 Loading model from {model_path}")
    model = PhoBERTClickbaitClassifier(model_name=model_path)
    
    # Predict on test set
    logger.info("🔮 Making predictions...")
    predictions = []
    probabilities_clickbait = []
    
    for i, text in enumerate(test_texts):
        if (i + 1) % 100 == 0:
            logger.info(f"   Processed {i + 1}/{len(test_texts)}")
        
        label, probs = model.predict(text, return_probs=True)
        predictions.append(label)
        probabilities_clickbait.append(probs[1])  # Probability of clickbait
    
    # Calculate metrics
    logger.info("\n📈 Calculating metrics...")
    
    precision, recall, f1, support = precision_recall_fscore_support(
        test_labels, predictions, average=None
    )
    
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        test_labels, predictions, average='weighted'
    )
    
    # ROC-AUC
    try:
        roc_auc = roc_auc_score(test_labels, probabilities_clickbait)
        logger.info(f"   ROC-AUC: {roc_auc:.4f}")
    except:
        roc_auc = None
        logger.warning("   Could not calculate ROC-AUC")
    
    # Confusion matrix
    cm = confusion_matrix(test_labels, predictions)
    tn, fp, fn, tp = cm.ravel()
    
    # Derived metrics
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    # Log results
    logger.info("\n" + "="*70)
    logger.info("📊 EVALUATION RESULTS")
    logger.info("="*70)
    
    logger.info("\n🔹 Per-class metrics:")
    logger.info(f"   Non-clickbait - Precision: {precision[0]:.4f}, Recall: {recall[0]:.4f}, F1: {f1[0]:.4f}")
    logger.info(f"   Clickbait     - Precision: {precision[1]:.4f}, Recall: {recall[1]:.4f}, F1: {f1[1]:.4f}")
    
    logger.info("\n🔹 Weighted metrics:")
    logger.info(f"   Precision: {precision_weighted:.4f}")
    logger.info(f"   Recall: {recall_weighted:.4f}")
    logger.info(f"   F1-score: {f1_weighted:.4f}")
    
    logger.info("\n🔹 Other metrics:")
    logger.info(f"   Sensitivity (True Positive Rate): {sensitivity:.4f}")
    logger.info(f"   Specificity (True Negative Rate): {specificity:.4f}")
    if roc_auc:
        logger.info(f"   ROC-AUC: {roc_auc:.4f}")
    
    logger.info("\n🔹 Confusion Matrix:")
    logger.info(f"   [[TN={tn:4d}  FP={fp:4d}]  (Predicted Negative)")
    logger.info(f"    [FN={fn:4d}  TP={tp:4d}]]  (Predicted Positive)")
    
    logger.info("\n" + "="*70)
    print(classification_report(
        test_labels, predictions,
        target_names=['Non-clickbait', 'Clickbait'],
        digits=4
    ))
    logger.info("="*70)
    
    # Save results as JSON
    results = {
        'model_path': model_path,
        'dataset_path': csv_path,
        'test_set_size': len(test_texts),
        'per_class_metrics': {
            'non_clickbait': {
                'precision': float(precision[0]),
                'recall': float(recall[0]),
                'f1': float(f1[0]),
                'support': int(support[0])
            },
            'clickbait': {
                'precision': float(precision[1]),
                'recall': float(recall[1]),
                'f1': float(f1[1]),
                'support': int(support[1])
            }
        },
        'weighted_metrics': {
            'precision': float(precision_weighted),
            'recall': float(recall_weighted),
            'f1': float(f1_weighted)
        },
        'other_metrics': {
            'sensitivity': float(sensitivity),
            'specificity': float(specificity),
            'roc_auc': float(roc_auc) if roc_auc else None
        },
        'confusion_matrix': {
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp)
        }
    }
    
    results_path = Path(output_dir) / 'evaluation_results.json'
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"\n✅ Results saved to {results_path}")
    
    # Plot confusion matrix
    try:
        _plot_confusion_matrix(cm, output_dir)
    except Exception as e:
        logger.warning(f"Could not plot confusion matrix: {e}")
    
    # Plot ROC curve
    if roc_auc:
        try:
            _plot_roc_curve(test_labels, probabilities_clickbait, roc_auc, output_dir)
        except Exception as e:
            logger.warning(f"Could not plot ROC curve: {e}")
    
    return results


def _plot_confusion_matrix(cm, output_dir):
    """Plot and save confusion matrix."""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    im = ax.imshow(cm, cmap='Blues', aspect='auto')
    
    # Add colorbar
    plt.colorbar(im, ax=ax)
    
    # Set ticks and labels
    classes = ['Non-clickbait', 'Clickbait']
    ax.set_xticks(np.arange(len(classes)))
    ax.set_yticks(np.arange(len(classes)))
    ax.set_xticklabels(classes)
    ax.set_yticklabels(classes)
    
    # Labels
    ax.set_xlabel('Predicted Label', fontsize=12)
    ax.set_ylabel('True Label', fontsize=12)
    ax.set_title('Confusion Matrix', fontsize=14, fontweight='bold')
    
    # Add text annotations
    for i in range(len(classes)):
        for j in range(len(classes)):
            text = ax.text(j, i, cm[i, j], ha="center", va="center", 
                         color="white" if cm[i, j] > cm.max() / 2 else "black",
                         fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    plot_path = Path(output_dir) / 'confusion_matrix.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    logger.info(f"✅ Confusion matrix saved to {plot_path}")
    plt.close()


def _plot_roc_curve(y_true, y_probs, roc_auc, output_dir):
    """Plot and save ROC curve."""
    fpr, tpr, _ = roc_curve(y_true, y_probs)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
    ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random classifier')
    
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title('ROC Curve', fontsize=14, fontweight='bold')
    ax.legend(loc="lower right", fontsize=11)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    
    plot_path = Path(output_dir) / 'roc_curve.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    logger.info(f"✅ ROC curve saved to {plot_path}")
    plt.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Evaluate PhoBERT clickbait classifier'
    )
    parser.add_argument(
        '--model-path',
        type=str,
        default=str(MODEL_DIR),
        help='Path to fine-tuned model'
    )
    parser.add_argument(
        '--csv-path',
        type=str,
        default=DATASET_CSV,
        help='Path to dataset CSV file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=str(EVALUATION_DIR),
        help='Directory to save evaluation results'
    )
    
    args = parser.parse_args()
    
    evaluate_model(
        model_path=args.model_path,
        csv_path=args.csv_path,
        output_dir=args.output_dir
    )
