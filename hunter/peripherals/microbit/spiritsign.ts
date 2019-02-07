let lean = ""
let msg = ""
input.onGesture(Gesture.Shake, function () {
    basic.showString(msg)
    basic.pause(2000)
    basic.clearScreen()
})
msg = ""
lean = ""
ghosthunter.startUp()
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
        msg = ghosthunter.decode()
        basic.showString(msg)
    }
})
