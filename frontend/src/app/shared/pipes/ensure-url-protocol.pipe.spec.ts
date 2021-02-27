import { EnsureUrlProtocolPipe } from "./ensure-url-protocol.pipe";

describe("EnsureUrlProtocolPipe", () => {
  let pipe: EnsureUrlProtocolPipe;

  beforeEach(() => {
    pipe = new EnsureUrlProtocolPipe();
  });

  it("create an instance", () => {
    expect(pipe).toBeTruthy();
  });

  it("should not prefix if already contains a protocol", () => {
    expect(pipe.transform("http://www.astrobin.com")).toEqual("http://www.astrobin.com");
    expect(pipe.transform("https://www.astrobin.com")).toEqual("https://www.astrobin.com");
    expect(pipe.transform("ftp://www.astrobin.com")).toEqual("ftp://www.astrobin.com");
    expect(pipe.transform("ssh://www.astrobin.com")).toEqual("ssh://www.astrobin.com");
  });

  it("should prefix if it does not contains a protocol", () => {
    expect(pipe.transform("www.astrobin.com")).toEqual("http://www.astrobin.com");
    expect(pipe.transform("astrobin.com")).toEqual("http://astrobin.com");
  });
});
