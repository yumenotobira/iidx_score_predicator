require 'nokogiri'

module TextageParser
  class Browser
    attr_accessor :html
    def initialize(html_file)
      #html = erase_script(html_file)
      #html = add_body(html)
      #@html = change_charset(html)
      @html = html_file
    end

    private
    def erase_script(html)
      html.gsub(/<script.+<\/script>/, '')
    end

    def change_charset(html)
      html.gsub(/charset=shift_jis/, "charset=utf-8")
    end

    def add_body(html)
      html.gsub(/<\/title>/, "</title></head><body>")
    end
  end
end
