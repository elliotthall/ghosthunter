let msg = ""
basic.showLeds(`
    # . # . #
    . # # # .
    # . # . #
    . . # . .
    . . # . .
    `)
basic.forever(function () {
    if (input.buttonIsPressed(Button.A)) {
        basic.clearScreen()
        while (true) {
            if (input.buttonIsPressed(Button.AB)) {
                basic.showString(ghosthunter.transmit(msg))
                msg = ""
                break;
            } else if (input.buttonIsPressed(Button.A)) {
                msg = "" + msg + "."
                basic.showString(msg)
            }
            if (input.buttonIsPressed(Button.B)) {
                msg = "" + msg + "-"
                basic.showString(msg)
            }
        }
    }
})
