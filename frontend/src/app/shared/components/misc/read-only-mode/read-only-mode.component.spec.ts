import { AppModule } from "@app/app.module";
import { MockBuilder, MockRender } from "ng-mocks";
import { ReadOnlyModeComponent } from "./read-only-mode.component";

describe("ReadOnlyModeComponent", () => {
  let component: ReadOnlyModeComponent;

  beforeEach(async () => MockBuilder(ReadOnlyModeComponent, AppModule));
  beforeEach(() => (component = MockRender(ReadOnlyModeComponent).point.componentInstance));

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
