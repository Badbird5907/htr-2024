from model import NICUBradycardiaModel
import torch

# Create a model with default parameters
model = NICUBradycardiaModel()
model.to(torch.bfloat16)
param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Model parameter count: {param_count}")