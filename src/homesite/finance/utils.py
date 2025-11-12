from homesite.utils import APP_ROOT, PRODUCTION_DATA, PRODUCTION_ENV, SECRETS

from datetime import datetime
import numpy as np
import pandas as pd
from pandas import DataFrame, Series
import plaid
from plaid.api import plaid_api
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from re import match

class Plaid:
    def __init__(self, enviroment: str) -> None:
        configuration = plaid.Configuration(
            host=plaid.Environment.Production if enviroment == "Production" else plaid.Environment.Sandbox,
            api_key={
                "clientId": SECRETS["plaid"]["client_id"],
                "secret": SECRETS["plaid"]["production_key"] if enviroment == "Production" else SECRETS["plaid"]["sandbox_key"],
            }
        )
        self.api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(self.api_client)

    def get_link_token(self, link_type) -> dict:
        request = dict(
            client_name="homesite-finance",
            user=dict(
                client_user_id="developer",
                phone_number="+1 512 7517358"
            ),
            language="en",
            country_codes=["US"],
            products=link_type,
            transactions=dict(days_requested=1)
        )

        return self.client.link_token_create(request).to_dict()

    def get_access_token(self, public_token: str) -> None:
        request = dict(public_token=public_token)

        return self.client.item_public_token_exchange(request).to_dict()
    
    def get_transactions(self, months: int):
        end_date = datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        start_date = end_date.replace(month=end_date.month - months, day=1)
        
        request = plaid_api.TransactionsGetRequest(
            access_token=SECRETS["plaid"]["chase_access_token"] if PRODUCTION_DATA else SECRETS["plaid"]["sandbox_transactions_access_token"],
            start_date=start_date,
            end_date=end_date
        )
        response = self.client.transactions_get(request)
        print(response)
        transactions: list = response['transactions']
        print(transactions)

        while len(transactions) < response['total_transactions']:
            request = plaid_api.TransactionsGetRequest(
                access_token=SECRETS["plaid"]["chase_access_token"] if PRODUCTION_DATA else SECRETS["plaid"]["sandbox_transactions_access_token"],
                start_date=start_date,
                end_date=end_date,
                options=dict(offset=len(transactions))
            )
            response = self.client.transactions_get(request)
            transactions.extend(response['transactions'])
        
        df = DataFrame(transactions)
        print(df)
        return df



class Categories:
    def __init__(self):
        def salary(transaction: Series):
            return match(r"^SAMSUNG AUSTIN S PAYROLL", transaction["description"]) and not bonus(transaction)

        def bonus(transaction: Series):
            return match(r"^SAMSUNG AUSTIN S PAYROLL", transaction["description"]) and transaction["amount"] == 7035.00

        def tithe(transaction: Series):
            return False

        def car_and_rental_insurance(transaction: Series):
            return match(r"^PROG COUNTY MUT", transaction["description"]) and transaction["amount"] < 0

        def gasoline(transaction: Series):
            return False

        def rent(transaction: Series):
            return match(r"^VENMO", transaction["description"]) and transaction["amount"] == -475.00

        def electric_bill(transaction: Series):
            return match(r"^BLUEBONNET ELECT", transaction["description"])

        def water_bill(transaction: Series):
            return False

        def groceries(transaction: Series):
            return False

        def benefits(transaction: Series):
            return False

        def retirement_savings(transaction: Series):
            return False

        def health_savings(transaction: Series):
            return False

        def sallie_mae(transaction: Series):
            return False

        def ed_financial(transaction: Series):
            return False

        def car_loan(transaction: Series):
            return match(r"^WELLS FARGO AUTO DRAFT", transaction["description"])

        def restaurants(transaction: Series):
            return False

        def games(transaction: Series):
            return match(r"^Microsoft\*Java Minecra", transaction["description"])

        def coffee(transaction: Series):
            return False

        def miscellaneous_expenditures(transaction: Series):
            return match(r"^VENMO", transaction["description"]) and not rent(transaction) and transaction["amount"] < 0 \
                or match(r"^Online Transfer to CHK ...0000", transaction["description"])

        self.categories_dict = {
            "receipts": {
                "salary": salary,
                "bonus": bonus,
            },
            "expenditures": {
                "necessities": {
                    "tithe": tithe,
                    "transportation": {
                        "car / rental insurance": car_and_rental_insurance,
                        "gasoline": gasoline
                    },
                    "lodging": {
                        "rent": rent
                    },
                    "utilities": {
                        "electric bill": electric_bill,
                        "water bill": water_bill
                    },
                    "groceries": groceries,
                    "benefits": benefits,
                    "savings": {
                        "retirement savings": retirement_savings,
                        "health savings": health_savings
                    },
                    "debts": {
                        "sallie mae": sallie_mae,
                        "ed financial": ed_financial,
                        "car loan": car_loan
                    }
                },
                "luxuries": {
                    "restaurants": restaurants,
                    "games": games,
                    "coffee": coffee
                },
                "misc expenditures": miscellaneous_expenditures
            }
        }

    def get_categories(self) -> list:
        def traverse_dictionary(data: dict, path=[]):
            for key, value in data.items():
                if isinstance(value, dict):
                    yield from traverse_dictionary(value, path + [key])
                else:
                    yield [path + [key], value]

        return list(traverse_dictionary(self.categories_dict))


class Transactions:
    def __init__(self, csv_filename: str, csv_profile: str, months: int = 6) -> None:
        self.plaid = Plaid("Production" if PRODUCTION_DATA else "Sandbox")
        self.df = self.get_transactions(csv_filename, csv_profile, months)
        self.categorize_transactions()

    def get_transactions(self, csv_filename: str, csv_profile: str, months: int) -> DataFrame:
        end = datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start = end.replace(month=end.month - months, day=1)
        
        if csv_profile == "chase":
            df = pd.read_csv(APP_ROOT / "data" / csv_filename, usecols=range(1, 7)).reset_index(drop=True)
            
            df = df.rename(columns={
                "Posting Date": "date",
                "Description": "description",
                "Amount": "amount",
                "Type": "type",
                "Balance": "balance",
                "Check or Slip #": "number"
            })

            df["date"] = pd.to_datetime(df["date"])
            df["amount"] = pd.to_numeric(df["amount"])
            df["balance"] = pd.to_numeric(df["balance"])
            df["number"] = pd.to_numeric(df["number"]).map(lambda num : -1 if num != num else int(num))
        
        else:
            raise ValueError(f"Unknown csv_profile: {csv_profile}")
        
        return df[(df["date"] >= start) & (df["date"] <= end)]
    
    def categorize_transactions(self) -> None:
        self.df["category"] = [[]] * len(self.df)

        categories = Categories().get_categories()
        def categorize_transaction(t: Series):
            for category in categories:
                labels, identifier = category
                if bool(identifier(t)):
                    if t["category"] == []:
                        t["category"] = labels
                    else:
                        raise Exception(f"""
                                Transaction mutiply identified
                                {t}
                                {t["category"]}
                                {labels}
                        """)
            return t
    
        self.df = self.df.apply(categorize_transaction, axis=1)

    def color_transactions(self) -> None:
        self.df["color"] = self.df["category"].apply(lambda categories: ",".join(categories))
        self.df = self.df.sort_values("color", axis=0, ignore_index=True)

        min = 25
        max = 100

        floor_interp = lambda a, b, x: int(a * (1 - x) + b * (x))

        def x_to_rgb(x: float) -> tuple[int, int, int]:
            match np.floor(6 * x):
                case 0:
                    x = 6 * x
                    return max, floor_interp(min, max, x), min
                case 1:
                    x = 6 * (x - 1/6)
                    return floor_interp(max, min, x), max, min
                case 2:
                    x = 6 * (x - 1/3)
                    return min, max, floor_interp(min, max, x)
                case 3:
                    x = 6 * (x - 1/2)
                    return min, floor_interp(max, min, x), max
                case 4:
                    x = 6 * (x - 2/3)
                    return floor_interp(min, max, x), min, max
                case 5:
                    x = 6 * (x - 5/6)
                    return max, min, floor_interp(max, min, x)
                case 6:
                    return max, min, min
            raise ValueError(f"Invalid x {x}")

        rgb_to_hex = lambda r, g, b: "#%s%s%s" % tuple([hex(c)[2:].rjust(2, "0") for c in (r, g, b)])

        def get_color_array(I: np.ndarray):
            X = I / len(self.df)
            h = [rgb_to_hex(*x_to_rgb(x)) for x in X]

            return h

        self.df["color"] = get_color_array(self.df.index.to_numpy(np.float64))

    def visualize_transactions(self) -> tuple[go.Figure, list[DataFrame], list[DataFrame], int]:

        self.color_transactions()

        base_font = 18
        title_font = int(base_font * 1.5)
        subplot_title_font = int(base_font * 1.25)

        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "domain"}, {"type": "domain"}]],
            subplot_titles=("Receipts", "Expenditures")
        )

        r = self.df[self.df["category"].apply(lambda categories: categories[0] == "receipts")].copy()
        r["category"] = r["category"].apply(lambda categories: categories[1:])
        e = self.df[self.df["category"].apply(lambda categories: categories[0] == "expenditures")].copy()
        e["amount"] = e["amount"].map(lambda amount: -amount)

        difference = sum(r["amount"]) - sum(e["amount"])
        if difference > 0:
            e = pd.concat([e, DataFrame({"category": [["surplus"]], "amount": [difference], "color": ["#00000000"]})])
        elif difference < 0:
            r = pd.concat([r, DataFrame({"category": [["deficit"]], "amount": [-difference], "color": ["#00000000"]})])

        frames: list[go.Frame] = []
        max_granularity = max([len(category) for category in self.df["category"]]) - 1
        
        receipt_agg_list, expenditure_agg_list = [], []
        for granularity in range(max_granularity + 1):
            get_category_by_granularity = lambda categories: categories[min(granularity, len(categories) - 1)]
            r["subcategory"] = r["category"].apply(get_category_by_granularity)
            e["subcategory"] = e["category"].apply(get_category_by_granularity)

            r_agg = r.groupby("subcategory").agg({"amount": "sum", "color": "first"})
            e_agg = e.groupby("subcategory").agg({"amount": "sum", "color": "first"})

            receipt_agg_list.append(r_agg["amount"])
            expenditure_agg_list.append(e_agg["amount"])

            if granularity == 1:
                fig.add_trace(
                    go.Pie(
                        labels=r_agg.index,
                        values=r_agg["amount"].values,
                        marker_colors=r_agg["color"].values,
                        name="Receipts",
                        textinfo="label+percent",
                        textfont=dict(size=base_font),
                    ), 1, 1,
                )
                fig.add_trace(
                    go.Pie(
                        labels=e_agg.index,
                        values=e_agg["amount"].values,
                        marker_colors=e_agg["color"].values,
                        name="Expenditures",
                        textinfo="label+percent",
                        textfont=dict(size=base_font),
                    ), 1, 2,
                )

            frames.append(go.Frame(
                name=str(granularity),
                data=[
                    go.Pie(
                        labels=r_agg.index,
                        values=r_agg["amount"].values,
                        marker_colors=r_agg["color"].values,
                        textinfo="label+percent",
                        textfont=dict(size=base_font),
                    ),
                    go.Pie(
                        labels=e_agg.index,
                        values=e_agg["amount"].values,
                        marker_colors=e_agg["color"].values,
                        textinfo="label+percent",
                        textfont=dict(size=base_font),
                    ),
                ]
            ))

        fig.frames = frames

        fig.update_layout(
            width=1200,
            height=600,
            font=dict(size=base_font),
            template="plotly_dark",
            legend=dict(font=dict(size=base_font)),
        )
        
        if "annotations" in fig.layout:
            for annot in fig.layout.annotations: # type: ignore
                try:
                    annot.font = dict(size=subplot_title_font)
                except Exception:
                    pass

        return fig, receipt_agg_list, expenditure_agg_list, max_granularity