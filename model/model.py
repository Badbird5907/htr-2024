import torch
import torch.nn as nn
import torch.nn.functional as F

class NICUHybridModel(nn.Module):
    def __init__(self, 
                 in_channels=3,       # e.g., ECG=1 channel, Resp=1 channel
                 seq_length=3000,     # e.g., ~6s at 500Hz or adjust as needed
                 out_channels=5,      # number of output classes for classification
                 cnn_channels=[64,128,128],
                 lstm_hidden_size=512,
                 lstm_num_layers=2,
                 reconstruction_loss=True):
        super(NICUHybridModel, self).__init__()
        
        # CNN feature extraction
        cnn_layers = []
        input_dim = in_channels
        for ch in cnn_channels:
            cnn_layers.append(nn.Conv1d(input_dim, ch, kernel_size=7, padding=3))
            cnn_layers.append(nn.BatchNorm1d(ch))
            cnn_layers.append(nn.ReLU(inplace=True))
            cnn_layers.append(nn.MaxPool1d(kernel_size=2, stride=2))
            input_dim = ch
        self.cnn = nn.Sequential(*cnn_layers)
        
        # After CNN pooling, sequence length is reduced by 2 for each MaxPool
        # final seq_length = seq_length / (2^(len(cnn_channels)))
        # feature dimension after CNN = cnn_channels[-1]
        cnn_out_dim = cnn_channels[-1]
        
        # LSTM for temporal modeling
        self.lstm = nn.LSTM(input_size=cnn_out_dim, 
                            hidden_size=lstm_hidden_size, 
                            num_layers=lstm_num_layers,
                            batch_first=True,
                            bidirectional=True)
        
        lstm_output_dim = lstm_hidden_size * 2
        
        # Classification Head
        self.fc_class = nn.Sequential(
            nn.Linear(lstm_output_dim, 256),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(256, out_channels)
        )
        
        # Reconstruction Head (Unsupervised)
        self.reconstruction_loss = reconstruction_loss
        if reconstruction_loss:
            self.decoder_fc = nn.Linear(lstm_output_dim, cnn_out_dim)
            dec_layers = []
            dec_input_dim = cnn_out_dim
            for ch in reversed(cnn_channels):
                dec_layers.append(nn.ConvTranspose1d(dec_input_dim, ch, kernel_size=4, stride=2, padding=1))
                dec_layers.append(nn.BatchNorm1d(ch))
                dec_layers.append(nn.ReLU(inplace=True))
                dec_input_dim = ch
            dec_layers.append(nn.Conv1d(dec_input_dim, in_channels, kernel_size=7, padding=3))
            self.decoder = nn.Sequential(*dec_layers)
        
    def forward(self, x, hidden=None):
        # x: (batch, in_channels, seq_length)
        c = self.cnn(x)  # (batch, cnn_out_dim, reduced_length)
        
        c = c.transpose(1, 2)  # (batch, reduced_length, cnn_out_dim)
        
        lstm_out, hidden = self.lstm(c, hidden)  # (batch, reduced_length, 2*lstm_hidden_size)
        
        # Classification: mean-pool over time
        cls_input = torch.mean(lstm_out, dim=1)  # (batch, lstm_output_dim)
        class_logits = self.fc_class(cls_input)  # (batch, out_channels)
        
        if self.reconstruction_loss:
            # Reconstruction
            dec_feats = self.decoder_fc(lstm_out)  # (batch, reduced_length, cnn_out_dim)
            dec_feats = dec_feats.transpose(1, 2)  # (batch, cnn_out_dim, reduced_length)
            reconstructed = self.decoder(dec_feats)  # (batch, in_channels, ~seq_length)
            return class_logits, reconstructed, hidden
        else:
            return class_logits, hidden 