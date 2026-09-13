from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import DecimalField, HiddenField, IntegerField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=128)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=256)])
    submit = SubmitField("Sign In")


class UploadOnlyMultipleFileField(MultipleFileField):
    """A file field whose object-backed initial value is always empty.

    ListingForm is initialized with ``obj=listing`` on edit. The Listing model has
    an ``images`` relationship with the same name as this upload field, but those
    persisted ListingImage rows are not uploaded files and must never become this
    field's data. Real files submitted in request form-data still populate the field
    through WTForms' normal ``process_formdata`` path.
    """

    def process_data(self, value):
        self.data = []


class ListingForm(FlaskForm):
    title = StringField("Working Title", validators=[Optional(), Length(max=80)])
    original_title = HiddenField()
    product_name = StringField("Product Name", validators=[Optional(), Length(max=255)])
    brand = StringField("Brand", validators=[Optional(), Length(max=128)])
    model_number = StringField("Model", validators=[Optional(), Length(max=128)])
    mpn = StringField("MPN", validators=[Optional(), Length(max=128)])
    gtin = StringField("GTIN", validators=[Optional(), Length(max=64)])
    condition = StringField("Condition", validators=[Optional(), Length(max=64)])
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1, max=9999)], default=1)
    final_price = DecimalField("Final Price (CAD)", validators=[Optional(), NumberRange(min=0.01)], places=2)
    original_final_price = HiddenField()
    seller_notes = TextAreaField("Seller Notes", validators=[Optional(), Length(max=10000)])
    visible_text_text = TextAreaField("Visible Text", validators=[Optional(), Length(max=10000)])
    search_terms_text = TextAreaField("Search Terms", validators=[Optional(), Length(max=10000)])
    attributes_text = TextAreaField("Attributes", validators=[Optional(), Length(max=10000)])
    images = UploadOnlyMultipleFileField("Photos", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "JPG, PNG, and WebP images only.")])
    submit = SubmitField("Save Draft")
