#!/bin/bash

ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -C "your_email@example.com" -N ""
ssh-copy-id -o PreferredAuthentications=password -o PubkeyAuthentication=no -i ~/.ssh/id_ed25519.pub $1@$2