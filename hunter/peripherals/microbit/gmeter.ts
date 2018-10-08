let reading = 0
function displayResult() {
    led.plotBarGraph(
    reading,
    10
    )
    control.waitMicros(20000)
}
function startup() {
    serial.writeString("Ready")
}
function hunt() {
    if (input.buttonIsPressed(Button.A)) {
        reading = ghosthunter.gMeterRead()
        images.iconImage(IconNames.SmallDiamond).showImage(0)
        control.waitMicros(2000)
        images.iconImage(IconNames.Target).showImage(0)
        control.waitMicros(2000)
        images.iconImage(IconNames.Diamond).showImage(0)
        control.waitMicros(2000)
        basic.clearScreen()
    }
    if (reading > 0) {
        displayResult()
        reading = 0
    }
}
startup()
basic.forever(function () {
    hunt()
    control.waitMicros(2000)
})
