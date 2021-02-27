import { AppModule } from "@app/app.module";
import { MockBuilder, MockRender } from "ng-mocks";
import { SubscriptionsRouterPageComponent } from "./subscriptions-router-page.component";

describe("SubscriptionsRouterPageComponent", () => {
  let component: SubscriptionsRouterPageComponent;

  beforeEach(() => MockBuilder(SubscriptionsRouterPageComponent, AppModule));
  beforeEach(() => (component = MockRender(SubscriptionsRouterPageComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
