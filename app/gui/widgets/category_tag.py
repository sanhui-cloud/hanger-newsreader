import customtkinter as ctk
from app.config import CATEGORY_COLORS, CATEGORY_LABELS


class CategoryTag(ctk.CTkLabel):
    """Colored pill label for source category or sentiment."""

    SENTIMENT_COLORS = {
        'positive': ('#16a34a', '#15803d'),
        'negative': ('#dc2626', '#b91c1c'),
        'neutral':  ('#6b7280', '#4b5563'),
        'mixed':    ('#d97706', '#b45309'),
    }

    def __init__(self, master, text: str, color_pair: tuple[str, str] | None = None,
                 **kwargs):
        fg = color_pair or ('#6b7280', '#4b5563')
        super().__init__(
            master,
            text=f' {text} ',
            fg_color=fg,
            text_color='white',
            corner_radius=4,
            font=ctk.CTkFont(size=10, weight='bold'),
            **kwargs,
        )

    @classmethod
    def for_category(cls, master, category: str, **kwargs) -> 'CategoryTag':
        label = CATEGORY_LABELS.get(category, category.title())
        colors = CATEGORY_COLORS.get(category, ('#6b7280', '#4b5563'))
        return cls(master, text=label, color_pair=colors, **kwargs)

    @classmethod
    def for_sentiment(cls, master, sentiment: str, **kwargs) -> 'CategoryTag':
        colors = cls.SENTIMENT_COLORS.get(sentiment, ('#6b7280', '#4b5563'))
        return cls(master, text=sentiment.title(), color_pair=colors, **kwargs)
