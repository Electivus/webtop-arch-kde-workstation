[[ -o interactive ]] || return

export ZSH=/usr/share/oh-my-zsh
ZSH_CUSTOM="$HOME/.config/oh-my-zsh/custom"
ZSH_CACHE_DIR="$HOME/.cache/oh-my-zsh"
mkdir -p "$ZSH_CUSTOM" "$ZSH_CACHE_DIR"
ZSH_THEME=robbyrussell
zstyle ':omz:update' mode disabled
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
source "$ZSH/oh-my-zsh.sh"
