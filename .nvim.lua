vim.keymap.set({'i','n'}, '<F4>', ':TermRun python %<CR>', { noremap = true})
vim.keymap.set({'i','n'}, '<F5>', ':TermSend python %<CR>', { noremap = true})


-- local builtin = require('telescope.builtin')
-- vim.api.nvim_del_keymap('n', '<C-p>')
-- vim.keymap.set('n', '<C-p>', builtin.find_files, {})

-- vim.keymap.set('n', '<C-p>', builtin.git_files, {})
vim.o.guifont = "UbuntuMono Nerd Font Mono:h11"
vim.cmd.colorscheme("dracula")
-- vim.cmd.colorscheme("onedark")
-- vim.cmd.colorscheme("catppuccin-mocha")
-- vim.cmd.colorscheme("catppuccin-macchiato")

require('telescope').setup{
  pickers = {
    -- Default configuration for builtin pickers goes here:
    -- picker_name = {
    git_files = {
        use_git_root = false,
        recurse_submodules = true,
    } --   picker_config_key = value,
    --   ...
    -- }
    -- Now the picker_config_key will be applied every time you call this
    -- builtin picker
  }
}


require('telescope').setup{
  defaults = {
    file_ignore_patterns = {
      "blender_files"
    }
  }
}
