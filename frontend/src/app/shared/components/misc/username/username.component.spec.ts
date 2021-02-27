import { AppModule } from "@app/app.module";
import { MockBuilder, MockRender } from "ng-mocks";
import { UsernameComponent } from "./username.component";

describe("UsernameComponent", () => {
  let component: UsernameComponent;

  beforeEach(() => MockBuilder(UsernameComponent, AppModule));
  beforeEach(() => (component = MockRender(UsernameComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
