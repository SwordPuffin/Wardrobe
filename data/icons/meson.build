application_id = 'io.github.swordpuffin.wardrobe'

scalable_dir = 'hicolor' / 'scalable' / 'apps'
install_data(
  scalable_dir / ('@0@.svg').format(application_id),
  install_dir: get_option('datadir') / 'icons' / scalable_dir
)

symbolic_dir = 'hicolor' / 'symbolic' / 'apps'
install_data(
  symbolic_dir / ('@0@-symbolic.svg').format(application_id),
  install_dir: get_option('datadir') / 'icons' / symbolic_dir
)

actions_dir = 'hicolor' / 'scalable' / 'actions'

actions_icons = [
  actions_dir / 'app-symbolic.svg',
  actions_dir / 'interface-symbolic.svg',
  actions_dir / 'shell-symbolic.svg',
  actions_dir / 'cursor-symbolic.svg',
  actions_dir / 'search-symbolic.svg',
  actions_dir / 'wallpaper-symbolic.svg',
  actions_dir / 'download-symbolic.svg',
  actions_dir / 'user-trash-symbolic.svg',
  actions_dir / 'arrow-left-symbolic.svg',
  actions_dir / 'arrow-right-symbolic.svg',
  actions_dir / 'zoom-in-symbolic.svg',
  actions_dir / 'web-browser-symbolic.svg'
]

install_data(
  actions_icons,
  install_dir: get_option('datadir') / 'icons' / actions_dir
)