import calendar

import matplotlib.pyplot as plt
import seaborn as sns
from utils import ensure_charts_path


async def save_pie_chart(df, filename):
    """
    Generate and save a pie chart of expenses by category.
    """
    ensure_charts_path()
    expenses_by_category = df.groupby("Category")["Price"].sum().reset_index()
    plt.figure(figsize=(10, 6))
    pie = plt.pie(
        expenses_by_category["Price"],
        autopct=lambda p: f'{p:.1f}% ({p*sum(expenses_by_category["Price"])/100:.2f} €)'
        if p > 5
        else "",
        startangle=90,
    )

    plt.legend(pie[0], expenses_by_category["Category"], loc="best")
    plt.axis("equal")
    plt.savefig(filename)
    plt.close()


async def save_trend_chart(df, filename):
    """
    Generate and save a line chart showing the trend of the top 3 expense categories by month.
    """
    ensure_charts_path()
    df["Month"] = df["Date"].dt.month
    top_categories = df.groupby("Category")["Price"].sum().nlargest(3).index
    top_categories_data = df[df["Category"].isin(top_categories)]
    expenses_by_month_category = (
        top_categories_data.groupby(["Month", "Category"])["Price"]
        .sum()
        .unstack(fill_value=0)
    )
    plt.figure(figsize=(10, 6))
    month_names = [calendar.month_name[i] for i in range(1, 13)]
    ax = expenses_by_month_category.plot(kind="line", marker="o", ax=plt.gca())
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names, rotation=45, ha="right")
    ax.set_xlabel("")
    plt.legend(title="Category", loc="upper right")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


async def save_stacked_bar_chart(df, filename):
    """
    Generate and save a stacked bar chart of monthly expenses by category.
    """
    ensure_charts_path()
    df["Month"] = df["Date"].dt.strftime("%B")
    monthly_expenses = (
        df.groupby(["Month", "Category"])["Price"].sum().unstack().fillna(0)
    )
    months_order = list(calendar.month_name[1:])
    monthly_expenses = monthly_expenses.reindex(months_order)
    plt.figure(figsize=(12, 8))
    ax = monthly_expenses.plot(kind="bar", stacked=True, width=0.8, zorder=3)
    ax.set_xticklabels(months_order, rotation=45, ha="right")
    ax.set_xlabel("")
    plt.legend(loc="upper right")
    plt.grid(True, zorder=0)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


async def save_heatmap(df, filename):
    """
    Generate and save a heatmap of monthly expense intensity by category.
    """
    ensure_charts_path()
    df["Month"] = df["Date"].dt.strftime("%B")
    heatmap_data = df.pivot_table(
        values="Price", index="Category", columns="Month", aggfunc="sum", fill_value=0
    )
    existing_months = [
        month for month in calendar.month_name[1:] if month in heatmap_data.columns
    ]
    heatmap_data = heatmap_data[existing_months]
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, fmt=".2f", annot=True, cmap="YlGnBu")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
