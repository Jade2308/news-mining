"""Training script for PhoBERT clickbait classifier"""
import torch
import pandas as pd
import logging
import numpy as np
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_recall_fscore_support, 
    classification_report,
    confusion_matrix
)
from tqdm import tqdm
from pathlib import Path
import json

from config import MODEL_DIR, DATASET_CSV

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClickbaitDataset(Dataset):
    """Dataset loader for Vietnamese clickbait classification."""
    
    def __init__(self, texts, labels, tokenizer, max_length=256):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = int(self.labels[idx])
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': torch.tensor(label, dtype=torch.long)
        }


def train_phobert(
    csv_path: str = DATASET_CSV,
    output_dir: str = str(MODEL_DIR),
    epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    val_split: float = 0.2,
    seed: int = 42
):
    """Fine-tune PhoBERT on Vietnamese clickbait dataset.
    
    Args:
        csv_path: Path to clickbait dataset CSV
        output_dir: Directory to save trained model
        epochs: Number of training epochs
        batch_size: Batch size for training and validation
        learning_rate: Learning rate for optimizer
        val_split: Validation set ratio
        seed: Random seed for reproducibility
    """
    
    # Set seeds for reproducibility
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"🚀 Starting training on {device}")
    
    model_name = "vinai/phobert-base"
    
    # Load dataset
    logger.info(f"📂 Loading dataset from {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"   Total samples: {len(df)}")
    
    texts = df['title'].tolist()
    # Map labels: clickbait → 1, non-clickbait → 0
    labels = [1 if str(label).lower().strip() == 'clickbait' else 0 
              for label in df['label']]
    
    n_clickbait = sum(labels)
    n_non_clickbait = len(labels) - n_clickbait
    logger.info(f"   Clickbait: {n_clickbait} | Non-clickbait: {n_non_clickbait}")
    
    # Train-validation split
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=val_split, random_state=seed, stratify=labels
    )
    
    logger.info(f"📊 Train/Val split: {len(train_texts)}/{len(val_texts)}")
    
    # Load model and tokenizer
    logger.info(f"🤖 Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=2
    )
    model.to(device)
    
    # Create datasets
    train_dataset = ClickbaitDataset(train_texts, train_labels, tokenizer)
    val_dataset = ClickbaitDataset(val_texts, val_labels, tokenizer)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # Optimizer and scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=0,
        num_training_steps=total_steps
    )
    
    best_f1 = 0
    training_history = {
        'train_loss': [],
        'val_loss': [],
        'val_precision': [],
        'val_recall': [],
        'val_f1': []
    }
    
    # Training loop
    logger.info(f"🏋️  Starting training for {epochs} epochs")
    logger.info(f"   Batch size: {batch_size}, Learning rate: {learning_rate}")
    logger.info("="*70)
    
    for epoch in range(epochs):
        logger.info(f"\n📌 Epoch {epoch + 1}/{epochs}")
        
        # Training phase
        model.train()
        total_loss = 0
        
        with tqdm(train_loader, desc="Training", leave=True) as pbar:
            for batch_idx, batch in enumerate(pbar):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                optimizer.zero_grad()
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                loss = outputs.loss
                loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                
                total_loss += loss.item()
                pbar.set_postfix({'loss': f'{loss.item():.4f}'})
        
        avg_train_loss = total_loss / len(train_loader)
        training_history['train_loss'].append(avg_train_loss)
        logger.info(f"   Average training loss: {avg_train_loss:.4f}")
        
        # Validation phase
        model.eval()
        val_loss = 0
        val_preds = []
        val_true = []
        
        with torch.no_grad():
            with tqdm(val_loader, desc="Validation", leave=True) as pbar:
                for batch in pbar:
                    input_ids = batch['input_ids'].to(device)
                    attention_mask = batch['attention_mask'].to(device)
                    labels = batch['labels'].to(device)
                    
                    outputs = model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels
                    )
                    
                    val_loss += outputs.loss.item()
                    logits = outputs.logits
                    preds = torch.argmax(logits, dim=1)
                    
                    val_preds.extend(preds.cpu().numpy())
                    val_true.extend(labels.cpu().numpy())
        
        avg_val_loss = val_loss / len(val_loader)
        training_history['val_loss'].append(avg_val_loss)
        
        # Calculate metrics
        precision, recall, f1, _ = precision_recall_fscore_support(
            val_true, val_preds, average='weighted'
        )
        
        training_history['val_precision'].append(precision)
        training_history['val_recall'].append(recall)
        training_history['val_f1'].append(f1)
        
        logger.info(f"   Validation loss: {avg_val_loss:.4f}")
        logger.info(f"   Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f}")
        
        # Save best model
        if f1 > best_f1:
            best_f1 = f1
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)
            logger.info(f"   ✨ New best model saved (F1: {f1:.4f})")
        
        # Print classification report
        logger.info("\n   Classification Report:")
        print(classification_report(
            val_true, val_preds,
            target_names=['Non-clickbait', 'Clickbait'],
            digits=4
        ))
        
        # Confusion matrix
        cm = confusion_matrix(val_true, val_preds)
        logger.info(f"   Confusion Matrix:")
        logger.info(f"   [[TN={cm[0,0]:4d}  FP={cm[0,1]:4d}]")
        logger.info(f"    [FN={cm[1,0]:4d}  TP={cm[1,1]:4d}]]")
    
    # Save training history
    history_path = Path(output_dir) / 'training_history.json'
    with open(history_path, 'w') as f:
        json.dump(training_history, f, indent=2)
    logger.info(f"✅ Training history saved to {history_path}")
    
    # Final summary
    logger.info("\n" + "="*70)
    logger.info("🎉 Training completed!")
    logger.info(f"   Best F1 score: {best_f1:.4f}")
    logger.info(f"   Model saved to: {output_dir}")
    logger.info("="*70)
    
    return best_f1


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Train PhoBERT for Vietnamese clickbait detection'
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
        default=str(MODEL_DIR),
        help='Directory to save trained model'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=3,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=16,
        help='Batch size for training and validation'
    )
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=2e-5,
        help='Learning rate for optimizer'
    )
    parser.add_argument(
        '--val-split',
        type=float,
        default=0.2,
        help='Validation set ratio (0-1)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    train_phobert(
        csv_path=args.csv_path,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        val_split=args.val_split,
        seed=args.seed
    )
