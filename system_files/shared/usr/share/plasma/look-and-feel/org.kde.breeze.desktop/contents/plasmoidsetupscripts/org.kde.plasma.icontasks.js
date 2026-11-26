// runs when plasma adds the task manager to a new panel: pin only konsole, no grouping
applet.currentConfigGroup = ["General"]
applet.writeConfig("launchers", "applications:org.kde.konsole.desktop")
applet.writeConfig("groupingStrategy", 0)
