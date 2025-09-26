from flask_wtf import FlaskForm as Form

from app.main.forms import UsaTextInputField


def test_UsaTextInputField_renders_zero(client_request):
    class FakeForm(Form):
        field = UsaTextInputField()

    form = FakeForm(field=0)
    html = form.field()
    assert 'value="0"' in html
