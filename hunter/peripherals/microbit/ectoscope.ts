let scanning = false
let reading = 0
reading = 0
scanning = false
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
        scanning = true
        basic.clearScreen()
        while (scanning == true) {
            if (input.buttonIsPressed(Button.B)) {
                scanning = false
            }
            reading = ghosthunter.ectoScan()
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