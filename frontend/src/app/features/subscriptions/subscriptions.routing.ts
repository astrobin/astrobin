import { Routes } from "@angular/router";
import { SubscriptionsBuyPageComponent } from "@features/subscriptions/pages/buy/subscriptions-buy-page.component";
import { SubscriptionsCancelledPageComponent } from "@features/subscriptions/pages/cancelled-page/subscriptions-cancelled-page.component";
import { SubscriptionsOptionsPageComponent } from "@features/subscriptions/pages/subscriptions-options-page/subscriptions-options-page.component";
import { SubscriptionsRouterPageComponent } from "@features/subscriptions/pages/subscriptions-router-page/subscriptions-router-page.component";
import { SubscriptionsViewPaymentsPageComponent } from "@features/subscriptions/pages/subscriptions-view-payments-page/subscriptions-view-payments-page.component";
import { SubscriptionsViewSubscriptionsPageComponent } from "@features/subscriptions/pages/subscriptions-view-subscriptions-page/subscriptions-view-subscriptions-page.component";
import { SubscriptionsSuccessPageComponent } from "@features/subscriptions/pages/success-page/subscriptions-success-page.component";
import { AuthGuardService } from "@shared/services/guards/auth-guard.service";

export const routes: Routes = [
  {
    path: "",
    component: SubscriptionsRouterPageComponent,
    children: [
      {
        path: "options",
        component: SubscriptionsOptionsPageComponent
      },
      {
        path: "view",
        component: SubscriptionsViewSubscriptionsPageComponent,
        canActivate: [AuthGuardService]
      },
      {
        path: "payments",
        component: SubscriptionsViewPaymentsPageComponent,
        canActivate: [AuthGuardService]
      },
      {
        path: "success",
        component: SubscriptionsSuccessPageComponent,
        canActivate: [AuthGuardService]
      },
      {
        path: "cancelled",
        component: SubscriptionsCancelledPageComponent,
        canActivate: [AuthGuardService]
      },
      {
        path: ":product",
        component: SubscriptionsBuyPageComponent,
        canActivate: [AuthGuardService]
      }
    ]
  }
];
