let msg = ""
input.onGesture(Gesture.Shake, function () {
    basic.clearScreen()
    basic.showString(ghosthunter.transmit(msg))
    msg = ""
})
basic.showLeds(`
    # . # . #
    . # # # .
    # . # . #
    . . # . .
    . . # . .
    `)
msg = ""
basic.forever(function () {
    if (input.buttonIsPressed(Button.A)) {
        msg = "" + msg + "."
        basic.showString(msg)
    } else if (input.buttonIsPressed(Button.B)) {
        msg = "" + msg + "-"
        basic.showString(msg)
    }
})
