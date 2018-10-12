let reading = 0
function displayResult()  {

}
function startup() {
    serial.writeString("Ready")
}
function hunt() {
    basic.showNumber(input.rotation(Rotation.Pitch))
    if (input.buttonIsPressed(Button.B)) {

    }
}
input.onGesture(Gesture.TiltRight, function () {

})
reading = 0
startup()
images.createImage(`
    # . . . #
    . # . # .
    . # # # .
    . # . # .
    # . . . #
    `).showImage(0)
basic.forever(function () {
    hunt()
    basic.pause(200)
})
