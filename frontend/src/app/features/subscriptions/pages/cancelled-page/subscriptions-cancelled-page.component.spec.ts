import { AppModule } from "@app/app.module";
import { MockBuilder, MockRender } from "ng-mocks";
import { SubscriptionsCancelledPageComponent } from "./subscriptions-cancelled-page.component";

describe("CancelledPageComponent", () => {
  let component: SubscriptionsCancelledPageComponent;

  beforeEach(() => MockBuilder(SubscriptionsCancelledPageComponent, AppModule));
  beforeEach(() => (component = MockRender(SubscriptionsCancelledPageComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
