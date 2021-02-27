import { AppModule } from "@app/app.module";
import { MockBuilder, MockRender } from "ng-mocks";
import { LoggedOutPageComponent } from "./logged-out-page.component";

describe("LoggedOutPageComponent", () => {
  let component: LoggedOutPageComponent;

  beforeEach(() => MockBuilder(LoggedOutPageComponent, AppModule));
  beforeEach(() => (component = MockRender(LoggedOutPageComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
