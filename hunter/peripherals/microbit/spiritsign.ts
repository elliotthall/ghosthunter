let lean = ""
lean = ""
basic.showIcon(IconNames.StickFigure)
basic.forever(function () {
    if (input.buttonIsPressed(Button.A)) {
        basic.clearScreen()
        while (true) {
            lean = ghosthunter.lean()
            if (input.buttonIsPressed(Button.B)) {
                break;
            }
            // basic.pause(500)
            if (lean == "L") {
                ghosthunter.moveLeft()
            } else if (lean == "R") {
                ghosthunter.moveRight()
            } else if (lean == "U") {
                ghosthunter.moveup()
            } else if (lean == "D") {
                ghosthunter.moveDown()
            }
            if (input.buttonIsPressed(Button.A)) {
                ghosthunter.select()
            }
            basic.pause(300)
        }
        basic.showString(ghosthunter.decode())
    }
})
