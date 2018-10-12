let result = 0
function displayResult()  {
    led.plotBarGraph(
    result,
    10
    )
}
// This function will communicate with the Pi. For
// testing purposes it returns an arbitrary value
function ectoScan()  {
    result = Math.random(11)
}
function hunt()  {
    if (input.buttonIsPressed(Button.A)) {
        ectoScan()
        images.createImage(`
            . . . . .
            . . . . .
            . . . . .
            . . . . .
            . . # . .
            `).showImage(0)
        control.waitMicros(2000)
        images.createImage(`
            . . . . .
            . . . . .
            . . . . .
            . . # . .
            . . # . .
            `).showImage(0)
        control.waitMicros(2000)
        images.createImage(`
            . . . . .
            # # # # #
            . # # # .
            . . # . .
            . . # . .
            `).showImage(0)
        control.waitMicros(2000)
        images.createImage(`
            # # # # #
            # # # # #
            . # # # .
            . . # . .
            . . # . .
            `).showImage(0)
        control.waitMicros(2000)
        basic.clearScreen()
    }
    if (result > 0) {
        displayResult()
        result = 0
    }
}
function startup()  {
    serial.writeString("R")
}
startup()
images.createImage(`
    # # # # #
    # # # # #
    . # # # .
    . . # . .
    . . # . .
    `).showImage(0)
basic.forever(() => {
    hunt()
    control.waitMicros(2000)
})
