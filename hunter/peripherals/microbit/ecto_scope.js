let reading = 0
reading = 0
ghosthunter.startUp()
images.createImage(`
    # # # # #
    # # # # #
    . # # # .
    . . # . .
    . . # . .
    `).showImage(0)
basic.forever(function () {
    if (input.buttonIsPressed(Button.A)) {
        basic.clearScreen()
        while (true) {
            reading = ghosthunter.ectoScan()
            if (input.buttonIsPressed(Button.B)) {
                break;
            }
            if (reading == 0) {
                images.createImage(`
                    . . . . .
                    . . . . .
                    . . . . .
                    . . . . .
                    . . # . .
                    `).showImage(0)
            } else if (reading <= 3) {
                images.createImage(`
                    . . . . .
                    . . . . .
                    . . . . .
                    . . # . .
                    . . # . .
                    `).showImage(0)
            } else if (reading <= 5) {
                images.createImage(`
                    . . . . .
                    . . . . .
                    . # # # .
                    . . # . .
                    . . # . .
                    `).showImage(0)
            } else if (reading <= 7) {
                images.createImage(`
                    . . . . .
                    # # # # #
                    . # # # .
                    . . # . .
                    . . # . .
                    `).showImage(0)
            } else if (reading <= 10) {
                images.createImage(`
                    # # # # #
                    # # # # #
                    . # # # .
                    . . # . .
                    . . # . .
                    `).showImage(0)
            }
            basic.pause(500)
        }
        basic.clearScreen()
    }
})
