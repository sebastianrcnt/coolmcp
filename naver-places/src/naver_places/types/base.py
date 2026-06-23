from pydantic import BaseModel, model_validator


class DropNoneModel(BaseModel):
    """Base model that drops keys whose value is null before validation.

    Naver frequently returns explicit JSON null for fields it has no data on
    (e.g. visitorReviewsTotal, visitorReviewsScore, roadAddress). Without this,
    such a null hits a non-optional field like `int = 0` and fails the WHOLE
    parse — turning one missing field into a hard error for the entire place or
    review. Dropping nulls lets each field's declared default apply; genuinely
    optional fields (default None) simply stay None.
    """

    @model_validator(mode="before")
    @classmethod
    def _drop_nulls(cls, data):
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data
