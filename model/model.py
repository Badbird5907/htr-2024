import torch
import torch.nn as nn
import torch.nn.functional as F

class NICUBradycardiaModel(nn.Module):
    def __init__(self, 
                 in_channels=2,
                 seq_length=3750,   # sequence length (15s at 250Hz)
                 hidden_size=1536,  # Large LSTM hidden size
                 lstm_layers=2, 
                 out_channels=2):
        super(NICUBradycardiaModel, self).__init__()
        
        # ---------------------
        # CNN Feature Extractor
        # Keep this relatively small
        # ---------------------
        self.cnn = nn.Sequential(
            nn.Conv1d(in_channels, 64, kernel_size=7, padding=3),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),
            
            nn.Conv1d(64, 128, kernel_size=7, padding=3),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),
            
            nn.Conv1d(128, 128, kernel_size=7, padding=3),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2)
        )
        
        # After 3 max pools (2x each), sequence_length reduces by a factor of 8
        # Output of CNN: (batch, 128, seq_length/8)
        # reduced_seq_len = seq_length/8 (for 3000, ~375)
        
        # Input to LSTM: 128 features from CNN
        # Bidirectional doubles hidden size output dimension
        self.lstm = nn.LSTM(
            input_size=128,
            hidden_size=hidden_size,
            num_layers=lstm_layers,
            batch_first=True,
            bidirectional=True
        )
        # LSTM output dim: 2 * hidden_size (for bidirection)
        
        lstm_output_dim = hidden_size * 2
        
        # ---------------------
        # Large Fully Connected Layers
        # 
        # For parameter counting:
        # A linear layer W with shape (fan_in, fan_out) has fan_in * fan_out params (plus biases ~ fan_out)
        # hidden_size=1536 means lstm_output_dim=3072
        
        self.fc1 = nn.Linear(lstm_output_dim, 8192)
        # Another large layer to get another big chunk of parameters:
        # from 8192 -> 4096: 8192 * 4096 ≈ 33.5 million params
        self.fc2 = nn.Linear(8192, 4096)
        
        # Finally, from 4096 -> 2 outputs (binary classification)
        self.fc_out = nn.Linear(4096, out_channels)
        
        self.dropout = nn.Dropout(p=0.2)
        
    def forward(self, x, hidden=None):
        # x: (batch, in_channels, seq_length)
        
        # Extract CNN features
        c = self.cnn(x)  # (batch, 128, seq_length/8)
        
        # Prepare for LSTM
        c = c.transpose(1, 2)  # (batch, seq_length/8, 128)
        
        # LSTM
        lstm_out, hidden = self.lstm(c, hidden)  # (batch, seq_length/8, 2*hidden_size)
        
        # Pool over time (mean or max). Let's do mean pooling:
        x = torch.mean(lstm_out, dim=1)  # (batch, 2*hidden_size) = (batch, 3072)
        
        # Large FC layers
        x = self.fc1(x)     # (batch, 8192)
        x = F.relu(x)
        x = self.dropout(x)
        
        x = self.fc2(x)     # (batch, 4096)
        x = F.relu(x)
        x = self.dropout(x)
        
        x = self.fc_out(x)  # (batch, 2)
        
        return x, hidden 