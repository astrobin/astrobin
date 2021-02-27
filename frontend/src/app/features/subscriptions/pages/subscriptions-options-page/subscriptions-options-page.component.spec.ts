import { AppModule } from "@app/app.module";
import { MockBuilder, MockRender } from "ng-mocks";
import { SubscriptionsOptionsPageComponent } from "./subscriptions-options-page.component";

describe("SubscriptionsOptionsPageComponent", () => {
  let component: SubscriptionsOptionsPageComponent;

  beforeEach(() => MockBuilder(SubscriptionsOptionsPageComponent, AppModule));
  beforeEach(() => (component = MockRender(SubscriptionsOptionsPageComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
