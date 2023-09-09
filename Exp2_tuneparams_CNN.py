from __future__ import print_function, division

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import torch.backends.cudnn as cudnn
import numpy as np
import torchvision
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt
import time
import os
import copy
import glob
from PIL import Image

cudnn.benchmark = True
# plt.ion()   # interactive mode


def run_experiment(EXP_EPOCHS, EXP_LR, folder):

    ################################################################################
    ##  Load data
    ################################################################################

    # Data augmentation and normalization for training
    # Just normalization for validation
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    data_dir = '../data/images/Exp2_TuneParams/' + folder
    image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x),
                                              data_transforms[x])
                      for x in ['train', 'val']}
    dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=4,
                                                 shuffle=True, num_workers=0)
                  for x in ['train', 'val']}
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
    class_names = image_datasets['train'].classes

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    ################################################################################
    ##  Visualize a few images
    ################################################################################

    def imshow(inp, title=None):
        """Imshow for Tensor."""
        inp = inp.numpy().transpose((1, 2, 0))
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        inp = std * inp + mean
        inp = np.clip(inp, 0, 1)
        plt.figure()
        plt.imshow(inp)
        if title is not None:
            plt.title(title)
        # plt.pause(10)  # pause a bit so that plots are updated


    # Get a batch of training data
    inputs, classes = next(iter(dataloaders['train']))

    # Make a grid from batch
    out = torchvision.utils.make_grid(inputs)

    imshow(out, title=[class_names[x] for x in classes])
    #plt.show()


    ################################################################################
    ##  Training the model
    ################################################################################
    def train_model(model, criterion, optimizer, scheduler, num_epochs):

        train_acc = []
        train_err = []
        test_acc = []
        test_err = []

        since = time.time()

        best_model_wts = copy.deepcopy(model.state_dict())
        best_acc = 0.0

        for epoch in range(num_epochs):
            print(f'Epoch {epoch}/{num_epochs - 1}')
            print('-' * 10)

            # Each epoch has a training and validation phase
            for phase in ['train', 'val']:
                if phase == 'train':
                    model.train()  # Set model to training mode
                else:
                    model.eval()   # Set model to evaluate mode

                running_loss = 0.0
                running_corrects = 0

                # Iterate over data.
                print('Iterate over data')
                # for inputs, labels in dataloaders[phase]:
                for i, (inputs, labels) in enumerate(dataloaders[phase]):
                    if i % 10 == 0:
    	                print(f'{i}/{len(dataloaders[phase])}')
                    inputs = inputs.to(device)
                    labels = labels.to(device)

                    # zero the parameter gradients
                    optimizer.zero_grad()

                    # forward
                    # track history if only in train
                    with torch.set_grad_enabled(phase == 'train'):
                        outputs = model(inputs)
                        _, preds = torch.max(outputs, 1)
                        loss = criterion(outputs, labels)

                        # backward + optimize only if in training phase
                        if phase == 'train':
                            loss.backward()
                            optimizer.step()

                    # statistics
                    running_loss += loss.item() * inputs.size(0)
                    running_corrects += torch.sum(preds == labels.data)

                    # #debug
                    # if i == 3:
                    #     break

                if phase == 'train':
                    scheduler.step()

                epoch_loss = running_loss / dataset_sizes[phase]
                epoch_acc = running_corrects.double() / dataset_sizes[phase]

                print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

                # deep copy the model
                if phase == 'val' and epoch_acc > best_acc:
                    best_acc = epoch_acc
                    best_model_wts = copy.deepcopy(model.state_dict())

                # record test accuracy 
                if phase == 'train':
                    train_acc.append(epoch_acc)
                    train_err.append(1 - epoch_acc)
                else: 
                    test_acc.append(epoch_acc)
                    test_err.append(1 - epoch_acc)
            print()

        time_elapsed = time.time() - since
        print(f'Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
        print(f'Best val Acc: {best_acc:4f}')

        # plot acc against epoch 
        plt.figure()
        plt.plot(range(1,num_epochs+1), train_acc, label = 'Train')
        plt.plot(range(1,num_epochs+1), test_acc, label = 'Test')
        plt.xlabel('num_epochs')
        plt.ylabel('accurracy')
        plt.legend()
        plt.title('CNN: accurracy vs. num_epochs')

        plt.figure()
        plt.plot(range(1,num_epochs+1), train_err, label = 'Train')
        plt.plot(range(1,num_epochs+1), test_err, label = 'Test')
        plt.xlabel('num_epochs')
        plt.ylabel('test error')
        plt.title('CNN: test error vs. num_epochs')
        # plt.show()

        # save plot and data
        filename = f'{folder}_cnn_epoch{EXP_EPOCHS}_lr{EXP_LR}'
        plt.savefig(f'output/{filename}.png')
        with open(f'output/{filename}.txt', 'w+') as f:
            f.write(f'train_acc: {[e.item() for e in train_acc]}\n')
            f.write(f'train_err: {[e.item() for e in train_err]}\n')
            f.write(f'test_acc: {[e.item() for e in test_acc]}\n')
            f.write(f'test_err: {[e.item() for e in test_err]}\n')

         
        # load best model weights
        model.load_state_dict(best_model_wts)
        return model

    ################################################################################
    ##  Visualizing model predictions
    ################################################################################

    def visualize_model(model, num_images=6):
        was_training = model.training
        model.eval()
        images_so_far = 0
        fig = plt.figure()

        with torch.no_grad():
            for i, (inputs, labels) in enumerate(dataloaders['val']):
                inputs = inputs.to(device)
                labels = labels.to(device)

                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)

                for j in range(inputs.size()[0]):
                    images_so_far += 1
                    ax = plt.subplot(num_images//2, 2, images_so_far)
                    ax.axis('off')
                    ax.set_title(f'predicted: {class_names[preds[j]]}')
                    imshow(inputs.cpu().data[j])

                    if images_so_far == num_images:
                        model.train(mode=was_training)
                        return
            model.train(mode=was_training)

    ################################################################################
    ##  Finetuning the convnet
    ################################################################################

    model_ft = models.resnet18(pretrained=True)
    num_ftrs = model_ft.fc.in_features
    # Here the size of each output sample is set to 2.
    # Alternatively, it can be generalized to nn.Linear(num_ftrs, len(class_names)).
    model_ft.fc = nn.Linear(num_ftrs, len(class_names))

    model_ft = model_ft.to(device)

    criterion = nn.CrossEntropyLoss()

    # Observe that all parameters are being optimized
    optimizer_ft = optim.SGD(model_ft.parameters(), lr=EXP_LR, momentum=0.9)

    # Decay LR by a factor of 0.1 every 7 epochs
    exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=7, gamma=0.1)


    ################################################################################
    ##  Train and evaluate
    ################################################################################
    model_ft = train_model(model_ft, criterion, optimizer_ft, exp_lr_scheduler,
                           num_epochs=EXP_EPOCHS)

pairs = ['Pair1_Birdo_Yoshi', 'Pair2_Bowser_MiniBowser', 'Pair3_Luigi_Mario','Pair4_Peach_Rosalina']
EXP_EPOCHS = 10
EXP_LRS = [0.0001, 0.001, 0.01]
# EXP_LRS = [0.0005, 0.002, 0.005]

for pair in pairs:
    # run_experiment(EXP_EPOCHS=25, EXP_LR=0.001, folder=pair)
    for EXP_LR in EXP_LRS:
        run_experiment(EXP_EPOCHS=EXP_EPOCHS, EXP_LR=EXP_LR, folder=pair)
    ## exit()


