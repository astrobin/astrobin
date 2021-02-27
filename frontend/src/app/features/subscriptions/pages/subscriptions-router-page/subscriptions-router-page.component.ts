import { Component, OnInit } from "@angular/core";
import { AuthService } from "@shared/services/auth.service";

@Component({
  selector: "astrobin-subscriptions-router-page",
  templateUrl: "./subscriptions-router-page.component.html",
  styleUrls: ["./subscriptions-router-page.component.scss"]
})
export class SubscriptionsRouterPageComponent implements OnInit {
  active: string;

  constructor(public authService: AuthService) {}

  ngOnInit(): void {
    if (location.pathname === "/subscriptions/options") {
      this.active = "options";
    } else if (location.pathname === "/subscriptions/view") {
      this.active = "view";
    } else if (location.pathname === "/subscriptions/payments") {
      this.active = "payments";
    } else if (location.pathname === "/subscriptions/lite") {
      this.active = "lite";
    } else if (location.pathname === "/subscriptions/premium") {
      this.active = "premium";
    } else if (location.pathname === "/subscriptions/ultimate") {
      this.active = "ultimate";
    }
  }
}
