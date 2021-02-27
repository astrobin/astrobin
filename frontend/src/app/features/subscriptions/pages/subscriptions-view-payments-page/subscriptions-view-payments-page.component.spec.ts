import { AppModule } from "@app/app.module";
import { MockBuilder, MockRender } from "ng-mocks";
import { SubscriptionsViewPaymentsPageComponent } from "./subscriptions-view-payments-page.component";

describe("SubscriptionsViewPaymentsPageComponent", () => {
  let component: SubscriptionsViewPaymentsPageComponent;

  beforeEach(() => MockBuilder(SubscriptionsViewPaymentsPageComponent, AppModule));
  beforeEach(() => (component = MockRender(SubscriptionsViewPaymentsPageComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
