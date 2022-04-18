let disableInput = document.getElementById("disable-input");
let btn = document.getElementById("disable-btn");

disableInput.addEventListener("input", () => {
  if (disableInput.value.trim().length > 0) {
    btn.disabled = false;
  } else {
    btn.disabled = true;
  }
});

if (disableInput.value.trim().length == 0) {
  btn.disabled = true;
}
