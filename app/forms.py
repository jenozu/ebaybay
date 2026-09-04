from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import IntegerField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=128)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=256)])
    submit = SubmitField("Sign In")


class ListingForm(FlaskForm):
    title = StringField("Working Title", validators=[Optional(), Length(max=255)])
    condition = StringField("Condition", validators=[Optional(), Length(max=64)])
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1, max=9999)], default=1)
    seller_notes = TextAreaField("Seller Notes", validators=[Optional(), Length(max=10000)])
    images = MultipleFileField("Photos", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "JPG, PNG, and WebP images only.")])
    submit = SubmitField("Save Draft")
