// replaces plasma-desktop's breeze layout: stock default panel, then kuubik tweaks
loadTemplate("org.kde.plasma.desktop.defaultPanel")

var desktopsArray = desktopsForActivity(currentActivity());
for( var j = 0; j < desktopsArray.length; j++) {
    desktopsArray[j].wallpaperPlugin = 'org.kde.image';
}

panels().forEach(function (panel) {
    panel.height = 40
    panel.floating = false
    panel.opacity = "opaque"

    panel.widgets("org.kde.plasma.showdesktop").forEach(function (w) { w.remove() })

    panel.widgets("org.kde.plasma.kickoff").forEach(function (w) {
        w.currentConfigGroup = ["General"]
        w.writeConfig("switchCategoryOnHover", true)
    })

    panel.widgets("org.kde.plasma.systemtray").forEach(function (w) {
        w.currentConfigGroup = ["General"]
        w.writeConfig("shownItems", ["org.kde.plasma.volume"])
        w.writeConfig("hiddenItems", ["org.kde.plasma.brightness", "org.kde.plasma.battery", "org.kde.plasma.clipboard"])
        w.writeConfig("disabledStatusNotifiers", ["plasmashell_microphone"])
    })

    panel.widgets("org.kde.plasma.digitalclock").forEach(function (w) {
        w.currentConfigGroup = ["Appearance"]
        w.writeConfig("showDate", false)
        // 2 = always 24h
        w.writeConfig("use24hFormat", 2)
    })
})
