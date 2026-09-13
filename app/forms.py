from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import DecimalField, HiddenField, IntegerField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=128)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=256)])
    submit = SubmitField("Sign In")


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
    images = MultipleFileField("Photos", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "JPG, PNG, and WebP images only.")])
    submit = SubmitField("Save Draft")

    def __init__(self, *args, **kwargs):
        # The Listing model also has an ``images`` relationship. When editing with
        # ``ListingForm(obj=listing)``, WTForms would otherwise use those persisted
        # ListingImage rows as the initial value for this upload-only field. If the
        # user saves without selecting a new file, the route then mistakes the model
        # rows for FileStorage objects and crashes while trying to read ``.stream``.
        # Keep existing images on the listing itself; this field represents only new
        # uploads selected in the current request.
        if kwargs.get("obj") is not None and "images" not in kwargs:
            kwargs["images"] = []
        super().__init__(*args, **kwargs)
