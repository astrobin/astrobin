import { AppModule } from "@app/app.module";
import { MockBuilder, MockRender } from "ng-mocks";
import { PermissionDeniedPageComponent } from "./permission-denied-page.component";

describe("PermissionDeniedPageComponent", () => {
  let component: PermissionDeniedPageComponent;

  beforeEach(() => MockBuilder(PermissionDeniedPageComponent, AppModule));
  beforeEach(() => (component = MockRender(PermissionDeniedPageComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
