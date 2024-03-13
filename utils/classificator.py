import torch
import torch.nn as nn

class Classificator(nn.Module):
    def __init__(self, num_classes, in_channels):
        super().__init__()

        self.skip1 = nn.Conv2d(in_channels, 32, 1, padding='same')
        self.conv_block1 = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, padding='same'),
            nn.BatchNorm2d(32),
            nn.ReLU(),
        )
        self.maxp1 = nn.MaxPool2d(2)

        self.skip2 = nn.Conv2d(32, 64, 1, padding='same')
        self.conv_block2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, padding='same'),
            nn.BatchNorm2d(64),
            nn.ReLU(),
        )
        self.maxp2 = nn.MaxPool2d(2)

        self.skip3 = nn.Conv2d(64, 128, 1, padding='same')
        self.conv_block3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding='same'),
            nn.BatchNorm2d(128),
            nn.ReLU(),
        )

        self.flatten = nn.Flatten()

        self.dropout = nn.Dropout(0.5)

        self.fc_block = nn.Sequential(
            # nn.Linear(30976, 512),
            # nn.ReLU(),

            nn.Linear(15488, 256),
            nn.ReLU(),
            
            #logits 
            nn.Linear(256, num_classes),
        )

    def forward(self,x):
        x1 = self.conv_block1(x) + self.skip1(x)
        x1 = self.maxp1(x1)

        x2 = self.conv_block2(x1) + self.skip2(x1)
        x2 = self.maxp2(x2)

        x3 = self.conv_block3(x2) + self.skip3(x2)
        x3 = self.flatten(x3)

        x3 = self.dropout(x3)

        x4 = self.fc_block(x3)

        return x4
