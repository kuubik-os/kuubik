source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

autoload -Uz compinit && compinit

# hotkeys (ctrl + arrow)
zmodload zsh/terminfo
# empty without a terminal (ssh commands, TERM=dumb)
[[ -n ${terminfo[kLFT5]} ]] && bindkey "${terminfo[kLFT5]}" backward-word
[[ -n ${terminfo[kRIT5]} ]] && bindkey "${terminfo[kRIT5]}" forward-word

# git branch
autoload -Uz vcs_info add-zsh-hook
add-zsh-hook precmd vcs_info
zstyle ':vcs_info:*' enable git
zstyle ':vcs_info:git:*' formats '(%b)'

# prompt
setopt prompt_subst
PROMPT='%n@%m%f %~%f > '
RPS1='%F{green}${vcs_info_msg_0_}%f'

# history
HISTFILE="$HOME/.zsh_history"
HISTSIZE=10000
SAVEHIST=10000
setopt hist_ignore_dups share_history

# other settings
setopt COMBINING_CHARS

# aliases
alias ls="eza -F --icons=auto --group-directories-first"
alias ll="eza -alF --git --icons=auto --group-directories-first"
alias la="eza -aF --git --icons=auto --group-directories-first"
alias l="ls"

alias cat="bat -P --decorations=never"
alias grep="rg"
alias find="fd"

alias ssh="TERM=xterm-256color ssh"

zstyle ':completion:*' menu select
zstyle ':completion:*' auto-description 'specify: %d'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' verbose yes
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

# remember, that file should end with newline
if [[ -f "$HOME/.zsh_paths" ]]; then
    while IFS= read -r dir; do
        [[ -z "$dir" || "$dir" == "#"* ]] && continue
        [[ -d "$dir" && ":${PATH}:" != *":$dir:"* ]] || continue
        export PATH="$dir:$PATH"
    done < "$HOME/.zsh_paths"
fi
