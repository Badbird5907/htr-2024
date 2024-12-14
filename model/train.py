import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from model import NICUBradycardiaModel
from datasets import load_from_disk

# Load the dataset
dataset = load_from_disk("HTR-2024-brachy")

# Create a DataLoader
train_loader = DataLoader(dataset, batch_size=32, shuffle=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = NICUBradycardiaModel(
    in_channels=2,
    seq_length=3750,   # 15s at 250Hz
    hidden_size=1536,  # Large LSTM hidden
    lstm_layers=2, 
    out_channels=2
).to(device)

criterion = nn.CrossEntropyLoss()  # Binary classification (2 classes)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

num_epochs = 10

for epoch in range(num_epochs):
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    
    for batch_idx, batch in enumerate(train_loader):
        # batch is a dictionary or tuple of (inputs, labels)
        inputs, labels = batch
        inputs = inputs.to(device)   # (batch, 2, 3750)
        labels = labels.to(device)   # (batch,)
        
        optimizer.zero_grad()
        
        outputs, _ = model(inputs)  # outputs: (batch, 2)
        loss = criterion(outputs, labels)
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * inputs.size(0)
        
        # Compute accuracy
        _, preds = torch.max(outputs, dim=1)
        correct = torch.sum(preds == labels).item()
        total_correct += correct
        total_samples += inputs.size(0)
    
    avg_loss = total_loss / total_samples
    accuracy = total_correct / total_samples * 100.0
    
    print(f"Epoch [{epoch+1}/{num_epochs}] | Loss: {avg_loss:.4f} | Accuracy: {accuracy:.2f}%")