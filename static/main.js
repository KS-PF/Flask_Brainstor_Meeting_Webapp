function FormCount(id, min_len, max_len) {
    let num_id = id + '-alart';
    let form_id = id;
    let value = String(document.getElementById(form_id).value);
    let form_count = document.getElementById(num_id)

    mes = '';

    min_len = Number(min_len)
    max_len = Number(max_len)
    let len = Number(value.length)

    if(len >= min_len && len <= max_len){
        mes = '良い状態です';
        form_count.classList.add('form-count-good');
        form_count.classList.remove('form-count-bad');
    }else{
        if(min_len == max_len){
            mes = String(min_len) + '文字で入力してください';
        }else{
            mes =  String(min_len) +'~'+ String(max_len) +'文字の間で入力してください';
        }
        form_count.classList.remove('form-count-good');
        form_count.classList.add('form-count-bad');
    }

    form_count.innerHTML =  value.length + '文字  ' +mes;
};




var getCssHamburger = document.getElementById('hamburger');
function HamburgerIn() {
    getCssHamburger.classList.toggle('active');
};
function HamburgerOut() {
    getCssHamburger.classList.remove('active');
};