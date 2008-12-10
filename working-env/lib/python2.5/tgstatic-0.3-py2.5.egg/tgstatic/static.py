import cherrypy
import turbogears
from turbogears import controllers, expose, validate, redirect
from os.path import dirname
import os, os.path
import shutil


def exec_and_ignore(f,*args,**kwargs):
    """ execute a function that might raise exceptions that we don't care about """
    try:
        f(*args,**kwargs)
    except:
        pass

def static():
    return cherrypy.session.get('static',False)

def base_url():
    return cherrypy.config.get('publish.base_url','')

def s_url(path):
    if not static():
        return path
    else:
        if not path.startswith('/static/'):
            path = path + ".html"
        if path.startswith('/'):
            path = base_url() + path
        return path


class StaticPublisher(controllers.Controller):
    publish_base_dir = "/tmp/"
    static_dir = ""
    root_methods = []
    def classes(self):
        """ needs to be overridden """
        return []

    @expose(template=".templates.admin_static_publish")
    def index(self):
        """ page with "publish" button and instructions or options """
        return
    
    @expose()
    def publish(self):
        """ writes a static version of the site data """
        cherrypy.session['static'] = True
        self.prepare_static_publish_dir()
        self.copy_tg_static_dirs()

        # main index and root methods
        for (m,fname) in self.root_methods:
            self.write_static_file(fname,m(cherrypy.root))


        for (model_class,controller_class,dir,index_limit) in self.classes(self):
            self.publish_class(model_class,controller_class,dir,index_limit)

            
        cherrypy.session['static'] = False
        return "done"

    def publish_class(self,model_class,controller_class,dir,index_limit=10):
        exec_and_ignore(os.makedirs,os.path.join(self.publish_base_dir,dir))
        count = self.publish_individual_pages(model_class,controller_class,dir)
        self.publish_indices(controller_class,dir,count,limit=index_limit)
        self.publish_additional(controller_class,dir)


    def publish_indices(self,controller_class,dir,count,limit=10):
        # we take count as an argument purely to speed things up a bit by not
        # doing an additional query. probably doesn't matter. 
        offsets = range(count)[0::limit]
        for offset in offsets:
            self.write_static_file("%s/index%d.html" % (dir,offset),
                                   controller_class.index(offset=offset,limit=limit))
        # duplicate the first one as index.html
        self.write_static_file("%s/index.html" % dir,
                               controller_class.index(offset=0))

    def publish_additional(self,controller_class,dir):
        """ any additional specific pages that need to be published """
        for (m,args,fname) in controller_class.static_additional_pages:
            self.write_static_file("%s/%s" % (dir,fname),
                                   m(controller_class,**args))

    def publish_individual_pages(self,model_class,controller_class,dir):
        items = model_class.select()
        count = items.count()
        for item in items:
            print str(item.id)
            self.write_static_file("%s/%d.html" % (dir,item.id),
                                   controller_class.default(item.id))
        return count

    def prepare_static_publish_dir(self):
        """ clean it out and make sure the right directory structure is set up """
        exec_and_ignore(os.makedirs,self.publish_base_dir)
        exec_and_ignore(shutil.rmtree,os.path.join(self.publish_base_dir,"static"))


    def copy_tg_static_dirs(self):
        """ copy everything in the static directories """
        shutil.copytree(self.static_dir,
                        os.path.join(self.publish_base_dir,"static"))

    def write_static_file(self,filename,content):
        filename = os.path.join(self.publish_base_dir,filename)
        f = open(filename,"w")
        f.write(content)
        f.close()
